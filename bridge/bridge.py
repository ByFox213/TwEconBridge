import asyncio
import json
import logging

import nats
from ddecon import AsyncECON
from dotenv import load_dotenv

from model import Env
from util import get_data_env, nats_connect

load_dotenv()
env = get_data_env(Env)


logging.basicConfig(
    level=getattr(logging, env.log_level.upper()),
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
        self.ns, self.js = await nats_connect(env)

        await self.econ.connect()
        await self.js.subscribe(
            f"teesports.{env.message_thread_id}",
            f"bridge_{env.message_thread_id}",
            cb=self.message_handler_bridge
        )
        logging.info("nats js subscribe \"teesports.%s\"", env.message_thread_id)

    async def message_handler_bridge(self, message):
        await message.in_progress()

        data = message.data.decode()
        await self.econ.message(
            data
            .replace("\"", "\\\"")
            .replace("\'", "\\\'")
            .replace("\\", "\\\\")
        )

        await message.ack()
        logging.debug("teesports.chat_id > %s", data)

    async def main(self):
        await self.connect()
        logging.info("nats connected and econ connected")

        if env.message_thread_id is None:
            raise ValueError("message_thread_id is None")
        logging.info("bridge launched")
        await self.message_checker()

    async def message_checker(self):
        logging.info("server_name=%s and message_thread_id=%s", env.server_name, env.message_thread_id)
        while True:
            try:
                message = await self.econ.read()
            except ConnectionError:
                if not env.reconnection:
                    logging.error("server: %s:%s dropped connection(ConnectionError)", (env.econ_host, env.econ_port))
                    break
                if not await self.econ.is_connected():
                    logging.debug("repeat: %s(%s:%s)", env.server_name, env.econ_host, env.econ_port)
                    self.econ = AsyncECON(env.econ_host, env.econ_port, env.econ_password)
                await asyncio.sleep(env.reconnection_time)
                continue

            if not message:
                await asyncio.sleep(0.5)
                continue

            try:
                text = message.decode()[:-3]
            except BaseException as ex:  # temp
                logging.exception(ex)
                logging.error("An error occurred during text processing \"%s\"", message)
                continue

            js = json.dumps(
                {
                    "server_name": env.server_name,
                    "message_thread_id": env.message_thread_id,
                    "text": text
                }
            )
            logging.debug("teesports.handler > %s", js)

            await self.js.publish(
                "teesports.handler",
                js.encode()
            )


if __name__ == '__main__':
    bridge = Bridge()
    asyncio.run(bridge.main())
