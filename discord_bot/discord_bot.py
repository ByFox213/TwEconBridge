import logging
import os

from dotenv import load_dotenv
from nextcord import Intents
from nextcord.ext.commands import Bot

from main_cog import Main

load_dotenv()

bot = Bot(intents=Intents.all(), owner_ids=[435836413523787778])

logging.basicConfig(
    level=logging.DEBUG,
    filename="discord_bot.log",
    format='%(asctime)s:%(levelname)s:%(name)s: %(message)s',
    encoding='utf-8',
    filemode="w"
)

text_bridge = os.getenv("text_bot_to_bridge", "[DS] {name}: {text}")
replace_channels = {}
for channel in os.getenv("replace_channels").split(" "):
    channel_ = channel.split(":")
    replace_channels[int(channel_[0])] = int(channel_[1])


if __name__ == '__main__':
    bot.add_cog(Main(
        bot=bot,
        replace_channels=replace_channels,
        text_bridge=text_bridge
    ))
    bot.run(os.getenv("DISCORD_BOT_TOKEN"))
