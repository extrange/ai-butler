from pathlib import Path

import nest_asyncio
import shortuuid
from dotenv import load_dotenv
from langchain.agents import AgentExecutor
from langchain.callbacks.base import CallbackManager
from langchain.callbacks.stdout import StdOutCallbackHandler
from langchain.chat_models import PromptLayerChatOpenAI
from langchain.memory import ConversationBufferMemory
from pyrogram.client import Client
from tools.reply import ReplyTool
from tools.telegram import (
    GetChatTool,
    GetUnreadMessagesTool,
    SearchContactTool,
    SendMessageTool,
)

from agents.base import BaseAgent

nest_asyncio.apply()


def main():
    # Load API keys
    load_dotenv(Path(__file__).parent / ".env", verbose=True)

    app = Client("telegram_account")
    app.start()

    run_uuid = shortuuid.uuid()[:10]

    chat = PromptLayerChatOpenAI(
        temperature=0,
        model_name="gpt-3.5-turbo",
        callback_manager=CallbackManager([StdOutCallbackHandler()]),
        verbose=True,
        client=None,
        pl_tags=[run_uuid, "base"],
    )

    telegram_chat = PromptLayerChatOpenAI(
        temperature=0,
        model_name="gpt-3.5-turbo",
        callback_manager=CallbackManager([StdOutCallbackHandler()]),
        verbose=True,
        client=None,
        pl_tags=[run_uuid, "telegram"],
    )

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    tools = [
        GetUnreadMessagesTool(client=app),
        SearchContactTool(client=app),
        SendMessageTool(client=app),
        GetChatTool(client=app),
        ReplyTool(),
    ]
    agent = BaseAgent.from_llm_and_tools(chat, tools)
    executor = AgentExecutor.from_agent_and_tools(agent, tools, memory=memory)

    tasks = [
        # "Send Chanel a poem using the content of the last few messages in the chat with her",
        # "Send Chanel a solution to her trading problem",
        # "summarize the content of my unread telegram messages",
        # "Which messages are important",
    ]

    for task in tasks:
        print(executor.run(input=task))

    while True:
        print(executor.run(input=input("Input: ")))


if __name__ == "__main__":
    main()
