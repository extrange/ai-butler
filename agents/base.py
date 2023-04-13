from __future__ import annotations
import re

import json
from typing import Any, List, Optional, Sequence, Tuple

from langchain.agents.agent import Agent
from langchain.callbacks.base import BaseCallbackManager
from langchain.chains import LLMChain
from langchain.prompts.base import BasePromptTemplate
from langchain.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
)
from langchain.schema import (
    AgentAction,
    AIMessage,
    BaseLanguageModel,
    BaseMessage,
    BaseOutputParser,
    HumanMessage,
)
from langchain.tools.base import BaseTool
from agents.prompts import FORMAT_INSTRUCTIONS, PREFIX, SUFFIX, TEMPLATE_TOOL_RESPONSE


class OutputParser(BaseOutputParser):
    format_instructions: str

    def get_format_instructions(self) -> str:
        return self.format_instructions

    def parse(self, text: str) -> Any:
        """
        More resilient version of parser.

        Searches for lines beginning with 'action:' and 'action_input:', and ignores preceding lines.
        """
        cleaned_output = text.strip()

        # Find line starting with 'action:'
        action_match = re.search("^action: (.*)$", cleaned_output, re.MULTILINE)
        if action_match is None:
            return {"action": "reply", "action_input": cleaned_output}
        action = action_match.group(1)

        action_input_match = re.search(
            "^action_input: (.*)", text, flags=re.MULTILINE | re.DOTALL
        )
        if action_input_match is None:
            return {"action": "reply", "action_input": cleaned_output}

        action_input = action_input_match.group(1)
        return {"action": action, "action_input": action_input}


class BaseAgent(Agent):
    """Base Agent"""

    output_parser: BaseOutputParser
    template_tool_response: str

    @property
    def finish_tool_name(self) -> str:
        return "reply"

    @property
    def _agent_type(self) -> str:
        raise NotImplementedError

    @property
    def observation_prefix(self) -> str:
        """Prefix to append the observation with."""
        return "Observation: "

    @property
    def llm_prefix(self) -> str:
        """Prefix to append the llm call with."""
        return "Thought:"

    @classmethod
    def create_prompt(
        cls,
        tools: Sequence[BaseTool],
        system_message: str = PREFIX,
        human_message: str = SUFFIX,
        input_variables: Optional[List[str]] = None,
        output_parser: Optional[BaseOutputParser] = None,
    ) -> BasePromptTemplate:
        tool_strings = "\n".join(
            [f"> {tool.name}: {tool.description}" for tool in tools]
        )
        tool_names = ", ".join([tool.name for tool in tools])
        _output_parser = output_parser or OutputParser(
            format_instructions=FORMAT_INSTRUCTIONS
        )
        format_instructions = human_message.format(
            format_instructions=_output_parser.get_format_instructions()
        )
        final_prompt = format_instructions.format(
            tool_names=tool_names, tools=tool_strings
        )
        if input_variables is None:
            input_variables = ["input", "chat_history", "agent_scratchpad"]
        messages = [
            SystemMessagePromptTemplate.from_template(system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessagePromptTemplate.from_template(final_prompt),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
        return ChatPromptTemplate(input_variables=input_variables, messages=messages)

    def _extract_tool_and_input(self, llm_output: str) -> Optional[Tuple[str, str]]:
        try:
            response = self.output_parser.parse(llm_output)
            return response["action"], response["action_input"]
        except Exception:
            raise ValueError(f"Could not parse LLM output: {llm_output}")

    def _construct_scratchpad(
        self, intermediate_steps: List[Tuple[AgentAction, str]]
    ) -> List[BaseMessage]:
        """Construct the scratchpad that lets the agent continue its thought process."""
        thoughts: List[BaseMessage] = []
        for action, observation in intermediate_steps:
            thoughts.append(AIMessage(content=action.log))
            human_message = HumanMessage(
                content=self.template_tool_response.format(observation=observation)
            )
            thoughts.append(human_message)
        return thoughts

    @classmethod
    def from_llm_and_tools(
        cls,
        llm: BaseLanguageModel,
        tools: Sequence[BaseTool],
        callback_manager: BaseCallbackManager | None = None,
        system_message: str = PREFIX,
        human_message: str = SUFFIX,
        template_tool_response: str = TEMPLATE_TOOL_RESPONSE,
        format_instructions: str = FORMAT_INSTRUCTIONS,
        input_variables: Optional[List[str]] = None,
        output_parser: Optional[BaseOutputParser] = None,
        **kwargs: Any,
    ) -> Agent:
        """Construct an agent from an LLM and tools."""
        cls._validate_tools(tools)
        _output_parser = output_parser or OutputParser(
            format_instructions=format_instructions
        )
        prompt = cls.create_prompt(
            tools,
            system_message=system_message,
            human_message=human_message,
            input_variables=input_variables,
            output_parser=_output_parser,
        )
        llm_chain = LLMChain(
            llm=llm,
            prompt=prompt,
            callback_manager=callback_manager,
        )
        tool_names = [tool.name for tool in tools]
        return cls(
            llm_chain=llm_chain,
            allowed_tools=tool_names,
            output_parser=_output_parser,
            template_tool_response=template_tool_response,
            **kwargs,
        )
