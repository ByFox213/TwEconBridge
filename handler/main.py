import asyncio
import json
import logging
import os
import re

import nats
from dotenv import load_dotenv

from emojies import replace_from_str
from model import Env, MsgHandler, Msg, RegexModel
from patterns import dd_patterns

load_dotenv()
env = Env(**os.environ)

logging.basicConfig(
    level=logging.DEBUG,
    filename="handler.log",
    format='%(asctime)s:%(levelname)s:%(name)s: %(message)s',
    encoding='utf-8',
    filemode="w"
)


class Handler:
    def __init__(self):
        self.ns = None
        self.js = None
        self.patterns = [
            RegexModel(name=name, regex=re.compile(regex), data=data)
            for name, (regex, data) in dd_patterns.copy().items()
        ]

    async def connect(self):
        self.ns = await nats.connect(
            servers=env.nats_server,
            user=env.nats_user,
            password=env.nats_password
        )
        self.js = self.ns.jetstream()

        await self.js.subscribe(
            f"teesports.handler",
            f"handler",
            cb=self.message_handler_bridge
        )
        logging.info("nats js subscribe \"teesports.handler\"")
        print("connected to econ and nats")

    async def message_handler_bridge(self, message):
        await message.in_progress()
        msg = MsgHandler(
            **json.loads(
                message.data.decode()
            )
        )
        name = None
        for pattern in self.patterns:
            regex = pattern.regex.findall(msg.text)
            if not regex:
                continue
            if len(regex[0]) == 2:
                name, text = regex[0]
            else:
                text = env.text.format(
                    player=regex[0],
                    text=pattern.data.format(
                        text_leave=env.text_leave,
                        text_join=env.text_join
                    )
                )
            js = Msg(
                message_thread_id=msg.message_thread_id,
                server_name=msg.server_name,
                type=pattern.name,
                name=name,
                text=replace_from_str(text)
            ).model_dump_json()
            logging.debug("teesports.messages > %s", js)
            await self.js.publish(f"teesports.messages", js.encode())
            break
        await message.ack()

    async def main(self):
        await self.connect()
        logging.info("nats connected and econ connected")
        while True:
            await asyncio.sleep(1)


if __name__ == '__main__':
    handler = Handler()
    asyncio.run(handler.main())
