import re

from pydantic import BaseModel, Field


class Env(BaseModel):
    nats_server: str = Field("127.0.0.1")
    nats_user: str = None
    nats_password: str = None
    log_level: str = Field("info")
    text: str = Field("{text}: {player}")
    text_leave: str = Field("leave player")
    text_join: str = Field("join player")
    nickname_regex: str | list = Field([])
    block_text_in_nickname: str | list = Field([["tw/", ""], ["twitch.tv/", ""]])
    chat_regex: str | list = Field([])
    block_text_in_chat: str | list = Field([])


class RegexModel(BaseModel):
    name: str
    regex: re.Pattern
    data: str


class Msg(BaseModel):
    server_name: str | None = None
    name: str | None = None
    message_thread_id: str | None = None
    regex_type: str | None
    text: str | None


class MsgHandler(BaseModel):
    server_name: str | None = None
    message_thread_id: str
    text: str
