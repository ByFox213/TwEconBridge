import asyncio
import json
import logging
import os

import nats
import yaml
from ddecon import AsyncECON
from dotenv import load_dotenv

from model import Env


def get_data_env(_env: Env) -> Env:
    if os.path.exists("./config.yaml"):
        with open('./config.yaml', encoding="utf-8") as fh:
            data = yaml.load(fh, Loader=yaml.FullLoader)
        _yaml = Env(**data) if data is not None else None
        if _yaml is not None:
            return _yaml
    return _env


load_dotenv()
env = get_data_env(Env(**os.environ))


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(name)s: %(message)s'
)


class Bridge:
    def __init__(self):
        self.econ = None
        self.ns = None
        self.js = None

    async def connect(self):
        self.econ = AsyncECON(
            env.econ_host,
            env.econ_port,
            env.econ_password,
            auth_message=env.auth_message.encode() if env.auth_message is not None else None
        )

        self.ns = await nats.connect(
            servers=env.nats_server,
            user=env.nats_user,
            password=env.nats_password
        )
        self.js = self.ns.jetstream()

        await self.econ.connect()
        await self.js.subscribe(
            f"teesports.{env.message_thread_id}",
            f"bridge_{env.message_thread_id}",
            cb=self.message_handler_bridge
        )
        logging.info("nats js subscribe \"teesports.%s\"", env.message_thread_id)
        print("connected to econ and nats")

    async def message_handler_bridge(self, message):
        await message.in_progress()

        data = message.data.decode()
        await self.econ.message(
            data
            .replace("\"", "\\\"")
            .replace("\'", "\\'")
            .replace("\\", "\\\\")
        )

        await message.ack()
        logging.debug("teesports.chat_id > %s", data)

    async def main(self):
        await self.connect()
        logging.info("nats connected and econ connected")

        if env.message_thread_id is None:
            raise ValueError("channel_id is None")
        await self.message_checker()

    async def message_checker(self):
        while True:
            try:
                message = await self.econ.read()
            except ConnectionError:
                if not await self.econ.is_connected() and env.reconnection:
                    logging.debug("repeat: %s(%s:%s)", (env.server_name, env.econ_host, env.econ_port))
                    self.econ = AsyncECON(env.econ_host, env.econ_port, env.econ_password)
                await asyncio.sleep(env.reconnection_time)
                continue

            if not message:
                await asyncio.sleep(0.5)
                continue

            js = json.dumps(
                {
                    "server_name": env.server_name,
                    "message_thread_id": env.message_thread_id,
                    "text": message.decode()[:-3]
                }
            )

            logging.debug("teesports.handler > %s", js)
            await self.js.publish("teesports.handler", js.encode())


if __name__ == '__main__':
    bridge = Bridge()
    asyncio.run(bridge.main())
