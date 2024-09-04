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

MESSAGE_THREAD_ID = os.getenv("MESSAGE_THREAD_ID")
nats_connect = {
    "servers": os.getenv("nats_server"),
    "user": os.getenv("nats_user"),
    "password": os.getenv("nats_password")
}
econ_connect = (os.getenv("econ_host"), os.getenv("econ_port"), os.getenv("econ_password"))

logging.basicConfig(
    level=logging.DEBUG,
    filename="bridge.log",
    filemode="w",
    format="%(asctime)s %(levelname)s %(message)s"
)


class Bridge:
    def __init__(self):
        self.econ = None
        self.nc = None
        self.js = None
        self.patterns = [re.compile(i) for _, i in dd_patterns.copy().items()]

    async def connect(self):
        self.econ = AsyncECON(*econ_connect)
        await self.econ.connect()

        self.nc = await nats.connect(**nats_connect)
        self.js = self.nc.jetstream()
        await self.js.subscribe(
            f"teesports.{MESSAGE_THREAD_ID}",
            f"bridge_{MESSAGE_THREAD_ID}",
            cb=self.message_handler_bridge
        )
        logging.info("nats js subscribe \"teesports.%s\"", MESSAGE_THREAD_ID)
        print("connected to econ and nats")

    async def message_handler_bridge(self, message):
        await message.in_progress()
        data = message.data.decode()
        await self.econ.message(data)
        await message.ack()
        logging.debug("teesports.chat_id > %s", data)

    async def main(self):
        await self.connect()
        logging.info("nats connected and econ connected")

        while True:
            message = await self.econ.read()
            if message:
                msg = message.decode()[:-3]
                for pattern in self.patterns:
                    regex = pattern.findall(msg)
                    if regex:
                        send_message = regex[0]
                        js = json.dumps({"chat_id": MESSAGE_THREAD_ID, "text": send_message})
                        logging.debug("teesports.messages > %s", js)
                        await self.js.publish("teesports.messages", js.encode())


if __name__ == '__main__':
    bridge = Bridge()
    asyncio.run(bridge.main())
