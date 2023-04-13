import asyncio
import re

from tools.reply import ReplyTool
import humanize
from langchain.chat_models import ChatOpenAI
from langchain.tools import BaseTool
from pyrogram.client import Client
from pyrogram.enums import ChatType
from pyrogram.types import Dialog, Message
from thefuzz import process

from agents.base import BaseAgent
from tools.base import BaseAgentTool
from tools.prompts import FORMAT_INSTRUCTIONS, PREFIX, SUFFIX
from tools.cache import cache
from pyrogram.enums import MessageMediaType

media_type_mapping = {
    MessageMediaType.AUDIO: "audio",
    MessageMediaType.DOCUMENT: "document",
    MessageMediaType.PHOTO: "photo",
    MessageMediaType.STICKER: "sticker",
    MessageMediaType.VIDEO: "video",
    MessageMediaType.ANIMATION: "animation",
    MessageMediaType.VOICE: "voice",
    MessageMediaType.VIDEO_NOTE: "video note",
    MessageMediaType.CONTACT: "contact",
    MessageMediaType.LOCATION: "location",
    MessageMediaType.VENUE: "venue",
    MessageMediaType.POLL: "poll",
    MessageMediaType.WEB_PAGE: "web page",
    MessageMediaType.DICE: "dice",
    MessageMediaType.GAME: "game",
}

chat_type_mapping = {
    ChatType.BOT: "Bot",
    ChatType.GROUP: "Group",
    ChatType.CHANNEL: "Group",
    ChatType.PRIVATE: "Person",
    ChatType.SUPERGROUP: "Group",
}


def telegram_agent_tool(llm: ChatOpenAI, client: Client):
    """
    Tool which uses an agent to perform tasks related to Telegram, which has access to following tools:

    - Finding contacts
    - Getting the latest messages from a chat
    - Sending messages
    - Replying to messages
    - Fetching the latest unread messages
    """
    tools = [
        GetUnreadMessagesTool(client=client),
        SearchContactTool(client=client),
        SendMessageTool(client=client),
        GetChatTool(client=client),
        ReplyTool(description="Use this to inform the user once the request has been completed."),
    ]
    agent = BaseAgent.from_llm_and_tools(
        llm=llm,
        tools=tools,
        system_message=PREFIX,
        human_message=SUFFIX,
        format_instructions=FORMAT_INSTRUCTIONS,
    )
    return BaseAgentTool(
        name="Telegram",
        description="Use for tasks related to Telegram, such as fetching, sending and replying to messages. Input is a sentence describing the task to do in detail, e.g. 'Tell Jordan that he is going overseas'.",
        tools=tools,
        llm=llm,
        agent=agent,
    )


class GetUnreadMessagesTool(BaseTool):
    """
    Get unread messages across all chats.

    Note: Limits to 10 messages per chat. Ignores channels.
    """

    name = "get_unread_messages"
    description = "Use this to fetch unread messages across all chats (up to 10 per chat). Takes null as input."
    client: Client

    def _run(self, tool_input: str) -> str:
        return asyncio.run(self._arun(tool_input))

    async def _arun(self, tool_input: str) -> str:
        # Limit to last 30 dialogs for now
        dialogs = [d async for d in self.client.get_dialogs(30)]
        if not dialogs:
            # No dialogs
            return "There are no unread messages."

        chats = []

        async def exclude_large_groups(dialog: Dialog) -> bool:
            """
            Filter only dialogs with unread mesages, less than 100 members
            """
            # Exclude chats without unread messages
            if not dialog.unread_messages_count:
                return False

            # Get full dialog type
            chat = await self.client.get_chat(dialog.chat.id)
            type = chat.type

            # Exclude groups > 100 people
            if type == ChatType.GROUP or type == ChatType.SUPERGROUP:
                return chat.members_count <= 100

            # Include only private and bot chats
            elif type == ChatType.BOT or type == ChatType.PRIVATE:
                return True
            else:
                return False

        # Filter dialogs
        dialogs = [d async for d in async_filter(exclude_large_groups, dialogs)]

        for dialog in dialogs:
            # Get unread messages (up to 10) from each chat
            count = (
                dialog.unread_messages_count
                if dialog.unread_messages_count < 10
                else 10
            )

            unread_msgs: list[Message] = [
                msg async for msg in self.client.get_chat_history(dialog.chat.id, 20)
            ]
            unread_msgs = unread_msgs[:count][::-1]  # Reverse order

            # Ignore dialogs without any text (e.g. xxx has join Telegram)
            if not any([msg.text for msg in unread_msgs]):
                continue

            msgs = [format_message(m) for m in unread_msgs]

            dialog_type = chat_type_mapping[dialog.chat.type]

            chats.append(
                f"Chat with {dialog.chat.title or dialog.chat.first_name} ({dialog_type})\n"
                f"================================\n" + "\n".join(msgs)
            )

        return "\n\n".join(chats)


async def async_filter(async_pred, iterable):
    for item in iterable:
        should_yield = await async_pred(item)
        if should_yield:
            yield item


class SearchContactTool(BaseTool):
    name = "search_contact"
    description = "Use this to find the chat id for a person/group given the name, e.g. for when you want to send a message. Input is a search string."
    client: Client

    def _run(self, tool_input: str) -> str:
        return asyncio.run(self._arun(tool_input))

    async def _arun(self, tool_input: str) -> str:
        # Check cache first
        if not "contacts" in cache:
            cache.set(
                key="contacts",
                value=[
                    (f"{user.first_name} {user.last_name or ''}", user.id)
                    for user in await self.client.get_contacts()
                ],
                expire=30 * 60,  # 30 mins
            )
        contacts = cache["contacts"]
        results = process.extractBests(
            query=tool_input,
            choices=contacts,
            # processor is run on BOTH query and choices...
            score_cutoff=50,
        )
        search_results = "\n".join(
            [f"{result[0][0]}: {result[0][1]}" for result in results]
        )

        # Also show latest contacts
        async def exclude_large_groups(dialog: Dialog):
            if dialog.chat.type == ChatType.CHANNEL:
                return False

            # Get full dialog type
            chat = dialog.chat
            type = chat.type

            # Exclude groups > 100 people
            if type == ChatType.GROUP or type == ChatType.SUPERGROUP:
                return chat.members_count <= 100

            # Include only private and bot chats
            elif type == ChatType.BOT or type == ChatType.PRIVATE:
                return True
            else:
                return False

        # Also include IDs of recent contacts/groups
        latest_dialogs_telegram = [d async for d in self.client.get_dialogs(30)]

        dialogs = [
            d async for d in async_filter(exclude_large_groups, latest_dialogs_telegram)
        ]

        latest_dialogs = []

        for d in dialogs:
            dialog_type = {
                ChatType.BOT: "Bot",
                ChatType.GROUP: "Group",
                ChatType.CHANNEL: "Group",
                ChatType.PRIVATE: "Person",
                ChatType.SUPERGROUP: "Group",
            }[d.chat.type]
            latest_dialogs.append(
                f"{d.chat.title or d.chat.first_name} ({dialog_type}): {d.chat.id}"
            )

        latest_dialogs_string = "\n".join([d for d in latest_dialogs])

        final_string = (
            f"Search results:\n" f"{search_results}\n" f"{latest_dialogs_string}"
        )

        return final_string


class GetChatTool(BaseTool):
    name = "get_chat_messages"
    description = "Gets the latest messages from a chat. Useful when you need to send/reply to messages. Input is the chat id, e.g. 19203049."
    client: Client

    def _run(self, tool_input: str) -> str:
        return asyncio.run(self._arun(tool_input))

    async def _arun(self, tool_input: str) -> str:
        match = re.search("\\-?\\d+", tool_input)
        if not match:
            return f"Invalid input: '{tool_input}'. Input must be a numeric chat id, e.g. 19203049."
        chat_id = match.group(0)

        # Fetch latest 20 messages
        try:
            msgs = [m async for m in self.client.get_chat_history(chat_id, 20)]
            msgs = msgs[::-1]  # reverse order
        except Exception as e:
            return str(e)

        return f"Messages:\n" + "\n".join([format_message(m) for m in msgs])


class SendMessageTool(BaseTool):
    name = "send_message"
    description = "Send a message to an id. Input is the chat id followed by the message, e.g. 19203049 I'll be going home late."
    client: Client

    def _run(self, tool_input: str) -> str:
        return asyncio.run(self._arun(tool_input))

    async def _arun(self, tool_input: str) -> str:
        chat_id, msg = tool_input.split(" ", 1)  # Split only the first comma
        try:
            await self.client.send_message(chat_id, msg)
            return f"Message sent successfully."
        except Exception as e:
            return str(e)


def format_message(m: Message) -> str:
    """
    Format messages in a human readable manner, e.g.:

    Chai Xun (10 hours ago): <photo> Nice
    """
    return f"{m.from_user.first_name} ({humanize.naturaltime(m.date)}): {f'<{media_type_mapping[m.media]}> ' if m.media else ''}{truncate_text(m.text or m.caption or '')}"


def truncate_text(text: str, max_len=500) -> str:
    """Truncate long messages"""
    if len(text) < max_len:
        return text.replace("\n", "\\n")

    return text[: max_len - 15].replace("\\n", " ") + "... (truncated)"
