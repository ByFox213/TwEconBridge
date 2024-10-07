import logging
import os
from typing import TypeVar, Callable

import nats
import yaml
from nats.aio.client import Client
from nats.js import JetStreamContext

DataClassT = TypeVar("DataClassT", bound="BaseModel")
_log = logging.getLogger(__name__)


__all__ = (
    "get_data_env",
    "nats_connect",
    ""
)


def get_env(modal: DataClassT) -> DataClassT:
    return modal(**os.environ)


def get_data_env(modal: DataClassT, func: Callable = get_env) -> DataClassT:
    if os.path.exists("./config.yaml"):
        with open('./config.yaml', encoding="utf-8") as fh:
            data = yaml.load(fh, Loader=yaml.FullLoader)
        _yaml = modal(**data) if data is not None else None
        if _yaml is not None:
            _log.info("config loaded from yaml")
            return _yaml
    _log.info("config loaded from env or custom")
    return func(modal)


async def nats_connect(env: DataClassT) -> tuple[Client, JetStreamContext]:
    nc = await nats.connect(
        servers=env.nats_server,
        user=env.nats_user,
        password=env.nats_password
    )
    js = nc.jetstream()
    _log.info("nats connected")
    return nc, js

