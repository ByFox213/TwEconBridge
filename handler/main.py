import asyncio
import json
import logging
import re
from datetime import datetime

from dotenv import load_dotenv

from emojies import replace_from_str
from model import Env, MsgHandler, Msg, RegexModel
from patterns import dd_patterns
from util import get_data_env, nats_connect
from util.main import format_mention, text_format, regex_format

load_dotenv()
env = get_data_env(Env)

logging.basicConfig(
    level=getattr(logging, env.log_level.upper()),
    format='%(asctime)s:%(levelname)s:%(name)s: %(message)s'
)


def generate_text(reg, pattern) -> tuple:
    if len(reg) == 2:
        return reg
    return None, format_mention(env.text.format(
        player=reg,
        text=pattern.data.format(
            text_leave=env.text_leave,
            text_join=env.text_join
        ))
    )


class Handler:
    def __init__(self):
        self.buffer = {}
        self.ns = None
        self.js = None
        self.patterns = [
            RegexModel(name=name, regex=re.compile(regex), data=data)
            for name, (regex, data) in dd_patterns.copy().items()
        ]
        self.chat_regex = ([
            (re.compile(regex), to) for regex, to in env.chat_regex
        ] if env.chat_regex is not None else [])
        self.nickname_regex = ([
            (re.compile(regex), to) for regex, to in env.nickname_regex
        ] if env.nickname_regex is not None else [])

    async def connect(self):
        self.ns, self.js = await nats_connect(env)

        await self.js.subscribe(
            "teesports.handler",
            "handler",
            cb=self.message_handler_bridge
        )
        logging.info("nats js subscribe \"teesports.handler\"")

    async def message_handler_bridge(self, message):
        await message.in_progress()
        msg = MsgHandler(
            **json.loads(
                message.data.decode()
            )
        )
        for pattern in self.patterns:
            regex = pattern.regex.findall(msg.text)
            if not regex:
                continue

            name, text = generate_text(regex[0], pattern)

            js = Msg(
                message_thread_id=msg.message_thread_id,
                server_name=msg.server_name,
                type=pattern.name,
                name=format_mention(
                    regex_format(
                        text_format(name, env.block_text_in_nickname), self.nickname_regex
                    )
                ),
                text=replace_from_str(
                    regex_format(
                        text_format(text, env.block_text_in_chat), self.chat_regex
                    )
                )
            ).model_dump_json()

            logging.debug("teesports.messages > %s", js)
            await self.js.publish(
                "teesports.messages",
                js.encode()
            )
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
