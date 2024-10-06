import ast
import asyncio
import json
import logging
import os
from itertools import cycle

import nats
import telebot.types
import yaml
from dotenv import load_dotenv
from nats.js import JetStreamContext
from telebot.async_telebot import AsyncTeleBot
from nats.aio.msg import Msg as MsgNats
from telebot.asyncio_helper import ApiTelegramException

from model import Env, Msg
from emojies import replace_from_emoji


def get_data_env(_env: Env) -> Env:
    if os.path.exists("./config.yaml"):
        with open('./config.yaml', encoding="utf-8") as fh:
            data = yaml.load(fh, Loader=yaml.FullLoader)
        _yaml = Env(**data) if data is not None else None
        if _yaml is not None:
            return _yaml
    return _env.model_copy(update={
        "TELEGRAM_BOT_TOKENS": ast.literal_eval(_env.TELEGRAM_BOT_TOKENS)
    })


load_dotenv()
env = get_data_env(Env(**os.environ))

bots = [
    AsyncTeleBot(token)
    for token in env.TELEGRAM_BOT_TOKENS
]  # Bypass rate limit
bot = bots[0]
bots = cycle(bots)

js: JetStreamContext = None
old_message_hash, count = 0, 0
buffer = {}

logging.basicConfig(
    level=getattr(logging, env.log_level.upper()),
    format='%(asctime)s:%(levelname)s:%(name)s: %(message)s'
)


def generate_message(_msg: telebot.types.Message, text: str = None) -> str:
    return env.text.format(
        name=_msg.from_user.first_name + (_msg.from_user.last_name or ''),
        text=replace_from_emoji(_msg.text)
        if text is None
        else text
        if _msg.caption is None
        else f"{text} | {_msg.caption}"
    )


def generate_message_reply(_msg: telebot.types.Message, text: str = '') -> str:
    return env.reply_string.format(
        replay_id=_msg.reply_to_message.id,
        replay_msg=generate_message(_msg.reply_to_message),
        id=_msg.id,
        msg=generate_message(_msg.reply_to_message)
    ) if (
            _msg.reply_to_message is not None and
            _msg.reply_to_message.text is not None
    ) else text


def check_media(message: telebot.types.Message) -> str:
    for i in [
        "sticker",
        "video",
        "photo",
        "audio",
        "voice"
    ]:
        if getattr(message, i) is not None:
            return generate_message(message, getattr(env, i + '_string'))
    return ""


async def message_handler_telegram(message: MsgNats):
    global old_message_hash, count
    """Takes a message from nats and sends it to telegram."""
    await message.in_progress()

    msg = Msg(**json.loads(message.data.decode()))
    logging.debug("teesports.%s > %s", msg.message_thread_id, msg.text)

    if buffer.get(msg.message_thread_id) is None:
        buffer[msg.message_thread_id] = ""

    text = f"{msg.name}: {msg.text}" if msg.name is not None else f"{msg.text}"
    buffer[msg.message_thread_id] += text + "\n"
    count += 1

    text_hash = hash(text)

    if old_message_hash != text_hash or count >= env.repetition:
        old_message_hash, count = text_hash, 0
        try:
            await next(bots).send_message(
                env.chat_id,
                buffer[msg.message_thread_id],
                message_thread_id=msg.message_thread_id
            )
        except ApiTelegramException:
            logging.debug("ApiTelegramException occurred")
        else:
            buffer[msg.message_thread_id] = ""

    return await message.ack()


async def main():
    global js
    nc = await nats.connect(
        servers=env.nats_server,
        user=env.nats_user,
        password=env.nats_password
    )
    js = nc.jetstream()
    logging.info("nats connected")

    # await js.delete_stream("teesports")
    await js.add_stream(name='teesports', subjects=['teesports.*'], max_msgs=5000)
    await js.subscribe("teesports.messages", "telegram_bot", cb=message_handler_telegram)
    logging.info("nats js subscribe \"teesports.messages\"")
    logging.info("bot is running")

    await bot.infinity_polling()


@bot.message_handler(content_types=["photo", "sticker", "sticker", "audio", "voice"])
async def echo_media(message: telebot.types.Message):
    if js is None or message is None:
        return

    text = (generate_message_reply(message) + check_media(message))[:255].encode()

    await js.publish(
        f"teesports.{message.message_thread_id}",
        text,
        headers={
            "Nats-Msg-Id": f"{message.from_user.id}_{message.date}_{hash(text)}_{message.chat.id}"
        }
    )


@bot.message_handler(content_types=["text"])
async def echo_text(message: telebot.types.Message):
    if js is None or message is None:
        return

    text = (generate_message_reply(message) + generate_message(message))[:255].encode()

    await js.publish(
        f"teesports.{message.message_thread_id}",
        text,
        headers={
            "Nats-Msg-Id": f"{message.from_user.id}_{message.date}_{hash(text)}_{message.chat.id}"
        }
    )


if __name__ == '__main__':
    asyncio.run(main())
