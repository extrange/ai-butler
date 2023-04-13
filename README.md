# AI Butler

Perform tasks on your behalf, such as:

- :speech_balloon: Summarize chats/emails, across multiple clients (Gmail, Telegram, WhatsApp)
- :email: (Auto) reply chats/emails, optionally with provided prompt (Gmail, Telegram, WhatsApp)
- :calendar: Add/modify calendar events (Gmail)
- :sun_behind_rain_cloud: Plan daily itinerary (based on todo list and prompt), taking into account weather
- :fork_and_knife: Meal planner: Suggestions on what to cook (Mealie)
- :globe_with_meridians: Browse the web and perform simple tasks

## Getting Started

```bash
python setup.py
```

Follow the instructions when prompted.

## Plugins

- Telegram ([Pyrogram][pyrogram])
- WhatsApp ([Baileys][baileys])
- Mail ([simplegmail][simplegmail])
- Calendar ([Google Calendar API][google-calendar-api])
- Document storage (TBD)

Daily summary message:
- 5 emails today. I archived 3 likely spam. I replied John thanking him for sending you the files. 
- 3 WhatsApp messages. I replied mum apologizing for coming home late last night. I saved an article Jane sent you and thanked her.  I'm not sure how to reply to Fred about GPT. 
- Weather will be rainy. Chanel wants to go hiking, but not recommended. You might want to play bridge instead. 
- For lunch today, you can try this recipe for oyster omelette, based on your conversations recently about low fodmap food.

## Image Support

Coming soon!

Candidate models:

- BLIP2
- GIT
- pix2struct
- ViT
- GLIP (for segmentation)

## Document/Image Search

Coming soon!

Features:

- Automatically categorize a document/image, and store/name it accordingly
- Retrieval

Candidate models:

- CLIP ViT family (image search)
- [Massive Text Embedding Leaderboard][massive-text-embedding]
- [Instructor Embedding][instructor-embedding]

## Limits

### Telegram

- 

## Open Source Models

- [gpt4-x-alpaca-13b-native-4bit][gpt4-x-alpaca-13b-native-4bit] (best)
- [vicuna-13b-4bit][vicuna-13b-4bit]
- [vicuna-7b-4bit][vicuna-7b-4bit]
- [ChatDoctor][chatdoctor]

[pyrogram]: https://github.com/pyrogram/pyrogram
[gpt4-x-alpaca-13b-native-4bit]: https://huggingface.co/anon8231489123/gpt4-x-alpaca-13b-native-4bit-128g
[vicuna-13b-4bit]: https://huggingface.co/eachadea/ggml-vicuna-13b-4bit
[vicuna-7b-4bit]: https://huggingface.co/eachadea/ggml-vicuna-7b-4bit
[chatdoctor]: https://github.com/Kent0n-Li/ChatDoctor
[baileys]: https://github.com/adiwajshing/Baileys
[simplegmail]: https://github.com/jeremyephron/simplegmail
[google-calendar-api]: https://developers.google.com/calendar/api/quickstart/python
[massive-text-embedding]: https://huggingface.co/spaces/mteb/leaderboard
[instructor-embedding]: https://github.com/HKUNLP/instructor-embedding