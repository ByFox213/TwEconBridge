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
    level=logging.INFO,
    filename="telegram_bot.log",
    format='%(asctime)s:%(levelname)s:%(name)s: %(message)s',
    encoding='utf-8',
    filemode="w"
)


async def message_handler_telegram(message: MsgNats):
    """Takes a message from nats and sends it to telegram."""
    await message.in_progress()
    msg = Msg(**json.loads(message.data.decode()))
    text = f"{msg.name}: {msg.text}" if msg.name is not None else f"{msg.text}"
    logging.debug("teesports.%s > %s", msg.channel_id, msg.text)

    if buffer.get(msg.channel_id) is None:
        buffer[msg.channel_id] = []

    if buffer[msg.channel_id]:
        text = "\n".join(buffer[msg.channel_id] + [text])
        buffer[msg.channel_id].clear()
    try:
        await next(bots).send_message(env.chat_id, text, message_thread_id=msg.channel_id)
    except ApiTelegramException:
        logging.debug("Заглушка ApiTelegramException")
        buffer[msg.channel_id].append(text)

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

    @bot.message_handler(func=lambda message: True)
    async def echo_to_bridge(message: telebot.types.Message):
        if not js or message is None:
            return

        await js.publish(
            f"teesports.{message.message_thread_id}",
            env.text_bot_to_bridge.format(
                name=message.from_user.first_name + (message.from_user.last_name or ''),
                text=replace_from_emoji(message.text)
            )[:255].encode()
        )

    await bot.infinity_polling()

if __name__ == '__main__':
    asyncio.run(main())
