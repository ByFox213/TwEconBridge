import asyncio
import json
import logging
import os
import re

import nats
from ddecon import AsyncECON
from dotenv import load_dotenv

from patterns import dd_patterns

load_dotenv()

channel_id = os.getenv("channel_id")


logging.basicConfig(
    level=logging.INFO,
    filename="bridge.log",
    format='%(asctime)s:%(levelname)s:%(name)s: %(message)s',
    encoding='utf-8',
    filemode="w"
)


class Bridge:
    def __init__(self):
        self.econ = None
        self.ns = None
        self.js = None
        self.patterns = [
            re.compile(i)
            for _, i in dd_patterns.copy().items()
        ]

    async def connect(self):
        self.econ = AsyncECON(
            os.getenv("econ_host"),
            int(os.getenv("econ_port")),
            os.getenv("econ_password")
        )
        self.ns = await nats.connect(
            servers=os.getenv("nats_server"),
            user=os.getenv("nats_user"),
            password=os.getenv("nats_password")
        )
        self.js = self.ns.jetstream()

        await self.econ.connect()
        await self.js.subscribe(
            f"teesports.{channel_id}",
            f"bridge_{channel_id}",
            cb=self.message_handler_bridge
        )
        logging.info("nats js subscribe \"teesports.%s\"", channel_id)
        print("connected to econ and nats")

    async def message_handler_bridge(self, message):
        await message.in_progress()
        data = message.data.decode()
        await self.econ.message(
            data
            .replace("\"", "\\\"")
            .replace("\'", "\\'")
        )
        await message.ack()
        logging.debug("teesports.chat_id > %s", data)

    async def main(self):
        await self.connect()
        logging.info("nats connected and econ connected")
        if channel_id is None:
            raise ValueError("channel_id is None")
        while True:
            message = await self.econ.read()
            if not message:
                await asyncio.sleep(0.5)
                continue
            msg = message.decode()[:-3]
            for pattern in self.patterns:
                regex = pattern.findall(msg)
                if not regex:
                    continue
                send_message = regex[0]
                js = json.dumps({
                    "channel_id": channel_id,
                    "text": send_message
                })
                logging.debug("teesports.messages > %s", js)
                await self.js.publish("teesports.messages", js.encode())


if __name__ == '__main__':
    bridge = Bridge()
    asyncio.run(bridge.main())
