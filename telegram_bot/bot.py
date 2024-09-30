import asyncio
import json
import logging
import os
from itertools import cycle

import nats
import telebot.types
from dotenv import load_dotenv
from telebot.async_telebot import AsyncTeleBot
from nats.aio.msg import Msg as MsgNats
from telebot.asyncio_helper import ApiTelegramException

from model import Env, Msg
from emojies import replace_from_emoji

load_dotenv()
env = Env(**os.environ)

bots = [
    AsyncTeleBot(token)
    for token in env.TELEGRAM_BOT_TOKENS.split(" ")
]  # Bypass rate limit
bot = bots[0]
bots = cycle(bots)

buffer = {}

logging.basicConfig(
    level=logging.DEBUG,
    filename="telegram_bot.log",
    format='%(asctime)s:%(levelname)s:%(name)s: %(message)s',
    encoding='utf-8',
    filemode="w"
)


def generate_message(_msg: telebot.types.Message, text: str = None) -> str:
    return env.text.format(
        name=_msg.from_user.first_name + (_msg.from_user.last_name or ''),
        text=replace_from_emoji(_msg.text)
        if text is None
        else text if _msg.caption is None
        else f"{text} | {_msg.caption}"
    )


def check_media(message: telebot.types.Message) -> str | None:
    for i in [
        "sticker",
        "video",
        "photo",
        "audio"
    ]:
        if getattr(message, i) is not None:
            return generate_message(message, getattr(env, "text_" + i))
    return None


async def message_handler_telegram(message: MsgNats):
    """Takes a message from nats and sends it to telegram."""
    await message.in_progress()
    msg = Msg(**json.loads(message.data.decode()))
    text = f"{msg.name}: {msg.text}" if msg.name is not None else f"{msg.text}"
    logging.debug("teesports.%s > %s", msg.message_thread_id, msg.text)

    if buffer.get(msg.message_thread_id) is None:
        buffer[msg.message_thread_id] = []

    if buffer[msg.message_thread_id]:
        text = "\n".join(buffer[msg.message_thread_id] + [text])
        buffer[msg.message_thread_id].clear()
    try:
        await next(bots).send_message(env.chat_id, text, message_thread_id=msg.message_thread_id)
    except ApiTelegramException:
        logging.debug("Заглушка ApiTelegramException")
        buffer[msg.message_thread_id].append(text)

    return await message.ack()


async def main():
    nc = await nats.connect(
        servers=env.nats_server,
        user=env.nats_user,
        password=env.nats_password
    )
    logging.info("nats connected")
    print("nats connected")
    js = nc.jetstream()

    # await js.delete_stream("teesports")
    await js.add_stream(name='teesports', subjects=['teesports.*'], max_msgs=5000)
    await js.subscribe("teesports.messages", "telegram_bot", cb=message_handler_telegram)
    logging.info("nats js subscribe \"teesports.messages\"")

    @bot.message_handler(content_types=["text", "photo", "sticker", "sticker", "audio"])
    async def echo_to_bridge(message: telebot.types.Message):
        if not js or message is None:
            return

        text = check_media(message)
        if text is None and message.text is not None:
            text = generate_message(message)

        replay = ""
        if message.reply_to_message is not None and message.reply_to_message.text is not None:
            replay = env.text_reply.format(
                replay_id=message.reply_to_message.id,
                replay_msg=generate_message(message.reply_to_message),
                id=message.id,
                msg=generate_message(message.reply_to_message)
            )

        await js.publish(
            f"teesports.{message.message_thread_id}",
            (replay + text)[:255].encode()
        )

    await bot.infinity_polling()


if __name__ == '__main__':
    asyncio.run(main())
