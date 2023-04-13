from pyrogram.client import Client
import humanize
from pprint import pprint
from tools.cache import cache
from thefuzz import process
from pyrogram.types import User, Dialog, Chat
from pyrogram.enums import ChatType, MessageMediaType
from tools.telegram import async_filter, truncate_text

# contacts: list[(str, int)] = cache["contacts"]
# for contact in contacts:
#     print(contact)
# while True:
#     results = process.extractBests(
#         query=input("input: "),
#         choices=contacts,
#         processor=lambda s: s[0] if type(s) is not str else s,
#         score_cutoff=50,
#     )
#     print("\n".join([f"{result[0][0]}: {result[0][1]}" for result in results]))
app = Client("telegram_account")

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


async def main():
    await app.start()
    # dialogs = [d async for d in app.get_dialogs(30)]
    chat = await app.get_chat("me")
    messages = [m async for m in app.get_chat_history("me", 10)]
    for m in messages:
        print(
            f"{m.from_user.first_name} ({humanize.naturaltime(m.date)}): {f'<{media_type_mapping[m.media]}> ' if m.media else ''}{truncate_text(m.text or m.caption or '')}"
        )

    # prof_chat = await app.get_chat(6160225620)
    # pprint([x async for x in app.get_chat_history(6160225620)])

    # async def exclude_large_groups(dialog: Dialog):
    #     if dialog.chat.type == ChatType.CHANNEL:
    #         return False

    #     # Get full dialog type
    #     chat = await app.get_chat(dialog.chat.id)
    #     type = chat.type

    #     # Exclude groups > 100 people
    #     if type == ChatType.GROUP or type == ChatType.SUPERGROUP:
    #         return chat.members_count <= 100

    #     # Include only private and bot chats
    #     elif type == ChatType.BOT or type == ChatType.PRIVATE:
    #         return True
    #     else:
    #         return False

    # for d in [d async for d in async_filter(exclude_large_groups,dialogs)]:
    #     dialog_type = {
    #         ChatType.BOT: "Bot",
    #         ChatType.GROUP: "Group",
    #         ChatType.CHANNEL: "Group",
    #         ChatType.PRIVATE: "Person",
    #         ChatType.SUPERGROUP: "Group",
    #     }[d.chat.type]
    #     print(f'{d.chat.title or d.chat.first_name} ({dialog_type}): {d.chat.id}')


import asyncio

asyncio.run(main())
