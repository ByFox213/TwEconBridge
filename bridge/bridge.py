import asyncio
import json
import logging
import os

import nats
from ddecon import AsyncECON
from dotenv import load_dotenv
from aiomultiprocess import Worker

from model import Env

load_dotenv()
env = Env(**os.environ)


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

    async def connect(self):
        self.econ = AsyncECON(env.econ_host, env.econ_port, env.econ_password)
        self.ns = await nats.connect(
            servers=env.nats_server,
            user=env.nats_user,
            password=env.nats_password
        )
        self.js = self.ns.jetstream()

        await self.econ.connect()
        await self.js.subscribe(
            f"teesports.{env.channel_id}",
            f"bridge_{env.channel_id}",
            cb=self.message_handler_bridge
        )
        logging.info("nats js subscribe \"teesports.%s\"", env.channel_id)
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
        if env.channel_id is None:
            raise ValueError("channel_id is None")
        await self.message_checker()

    async def message_checker(self):
        while True:
            message = await self.econ.read()
            if not message:
                await asyncio.sleep(0.5)
                continue
            js = json.dumps(
                {
                    "server_name": env.server_name,
                    "channel_id": env.channel_id,
                    "text": message.decode()[:-3]
                }
            )
            logging.debug("teesports.handler > %s", js)
            await self.js.publish("teesports.handler", js.encode())


if __name__ == '__main__':
    bridge = Bridge()
    asyncio.run(bridge.main())
