from pydantic import BaseModel, Field


class Env(BaseModel):
    TELEGRAM_BOT_TOKENS: str
    chat_id: str
    nats_server: str = Field("127.0.0.1")
    nats_user: str = None
    nats_password: str = None
    text: str = Field("[TG] {name}: {text}")
    text_sticker: str = Field("[STICKER]")
    text_video: str = Field("[MEDIA]")
    text_photo: str = Field("[PHOTO]")
    text_audio: str = Field("[AUDIO]")
    text_reply: str = Field("[Reply {replay_id}] {msg}\n")


class Msg(BaseModel):
    server_name: str | None = None
    name: str | None = None
    message_thread_id: str | None = None
    type: str | None
    text: str | None
