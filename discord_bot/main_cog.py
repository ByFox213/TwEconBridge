import json
import logging
import os
from typing import Callable

import nats
import nextcord
from nextcord import ActivityType, Status
from nextcord.ext import commands
from nextcord.ext.commands import Bot


async def nats_connect(func: Callable):
    nc = await nats.connect(
        servers=os.getenv("nats_servers"),
        user=os.getenv("nats_user"),
        password=os.getenv("nats_password")
    )
    logging.info("nats connected")
    print("| nats connected")
    js = nc.jetstream()

    await js.add_stream(name='teesports', subjects=['teesports.*'], max_msgs=5000)
    await js.subscribe("teesports.messages", "discord_bot", cb=func)
    logging.info("nats js subscribe \"teesports.messages\"")
    return nc, js


class Main(commands.Cog):
    def __init__(
            self,
            bot: Bot,
            replace_channels: dict,
            text_bridge: str
            ):
        self.bot: Bot = bot
        self.replace_channels = replace_channels
        self.channels_id = {i: o for o, i in replace_channels.copy().items()}
        self.text_bridge: str = text_bridge
        self.channels = {}
        self.ready: bool = False
        self.nc = None
        self.js = None

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.ready:
            print(f"| start {self.bot.user} (ID: {self.bot.user.id})")
            logging.info(f"start {self.bot.user} (ID: {self.bot.user.id})")
            self.nc, self.js = await nats_connect(self.message_handler_discord)
            await self.bot.change_presence(
                activity=nextcord.Activity(
                    type=ActivityType.watching,
                    name="🦊"),
                status=Status.online
            )
            self.ready: bool = True

    @commands.Cog.listener()
    async def on_http_ratelimit(self, limit, remaining, reset_after, bucket, scope):
        print(f"| ratelimit: {limit}, {remaining}, {reset_after}, {bucket}, {scope}")

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if message.author.bot or message.channel is None or self.js is None:
            return
        ch = self.channels_id.get(message.channel.id)
        if ch is None:
            return
        await self.js.publish(
            f"teesports.{ch}",
            self.text_bridge.format(name=message.author.display_name, text=message.content).encode()
        )

    async def message_handler_discord(self, message):
        await message.in_progress()
        if self.js is None:
            return
        msg = json.loads(message.data.decode())
        logging.debug("teesports.{chat_id}} > %s", msg)
        text = " ".join(msg["text"]) if isinstance(msg["text"], list) else msg["text"]
        channel_id = self.replace_channels.get(int(msg.get("channel_id")))
        ch = self.channels.get(channel_id)
        if ch is None:
            ch = self.bot.get_channel(channel_id)
            if ch is None:
                return await message.ack()
            self.channels[channel_id] = ch
        await ch.send(text)
        await message.ack()
