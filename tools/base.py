from langchain.tools import BaseTool
from typing import Type
from typing import Sequence
import asyncio
from langchain.memory.chat_memory import BaseChatMemory
from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.agents import AgentExecutor, BaseSingleActionAgent
from abc import ABC, abstractmethod
from agents.base import BaseAgent



class BaseAgentTool(BaseTool, ABC):
    """
    Base class for tools which use an agent internally.
    """

    memory: BaseChatMemory = ConversationBufferMemory(
        memory_key="chat_history", return_messages=True
    )
    llm: ChatOpenAI
    agent: BaseSingleActionAgent
    tools: Sequence[BaseTool]

    def _run(self, tool_input: str) -> str:
        return asyncio.run(self._arun(tool_input))

    async def _arun(self, tool_input: str) -> str:
        # Clear memory prior to every run
        self.memory.clear()

        executor = AgentExecutor.from_agent_and_tools(
            self.agent, self.tools, memory=self.memory
        )
        return executor.run(input=tool_input)
    