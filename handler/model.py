import re

from pydantic import BaseModel, Field


class Env(BaseModel):
    nats_server: str = Field("127.0.0.1")
    nats_user: str = None
    nats_password: str = None
    text: str = Field("{text}: {player}")
    text_leave: str = Field("leave player")
    text_join: str = Field("join player")


class RegexModel(BaseModel):
    name: str
    regex: re.Pattern
    data: str


class Msg(BaseModel):
    server_name: str | None = None
    name: str | None = None
    message_thread_id: str | None = None
    type: str | None
    text: str | None


class MsgHandler(BaseModel):
    server_name: str | None = None
    message_thread_id: str
    text: str

