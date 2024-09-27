from pydantic import BaseModel, Field


class Env(BaseModel):
    TELEGRAM_BOT_TOKENS: str
    chat_id: str
    nats_server: str = Field("127.0.0.1")
    nats_user: str = None
    nats_password: str = None
    text_bot_to_bridge: str = Field("[TG] {name}: {text}")


class Msg(BaseModel):
    server_name: str | None = None
    name: str | None = None
    channel_id: str | None = None
    type: str | None
    text: str | None
