import re

from pydantic import BaseModel, Field


class Env(BaseModel):
    nats_server: str = Field("127.0.0.1")
    nats_user: str = None
    nats_password: str = None


class RegexModel(BaseModel):
    name: str
    regex: re.Pattern


class Msg(BaseModel):
    server_name: str | None = None
    name: str | None = None
    channel_id: str | None = None
    type: str | None
    text: str | None


class MsgHandler(BaseModel):
    server_name: str | None = None
    channel_id: str
    text: str

