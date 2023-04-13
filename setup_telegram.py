from rich import print
import sys
from pyrogram.client import Client
from rich.prompt import Prompt, IntPrompt
import asyncio
from rich.console import Console

console = Console()
TELEGRAM_ACCOUNT = "telegram_account"


async def main():
    """
    Authorize Telegram API access.
    """

    # Check if Telegram is already setup
    app = Client(TELEGRAM_ACCOUNT)

    try:
        await app.connect()
        print(f"Telegram API has already been setup!")
    except AttributeError:
        await setup_telegram()

    sys.exit()


async def setup_telegram():
    console.clear()
    print(
        "Please visit https://my.telegram.org/apps to get your [blue]api_id[/blue] and [blue]api_hash[/blue]"
    )
    api_id = IntPrompt.ask("Enter your [blue]api_id[/blue]")
    api_hash = Prompt.ask("Enter your [blue]api_hash[/blue]")

    app = Client(TELEGRAM_ACCOUNT, api_id=api_id, api_hash=api_hash)
    await app.start()
    await app.authorize()

    print("Telegram API setup successfully")


if __name__ == "__main__":
    asyncio.run(main())
