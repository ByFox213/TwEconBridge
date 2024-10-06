from pydantic import BaseModel, Field


class Env(BaseModel):
    TELEGRAM_BOT_TOKENS: str | list = None
    chat_id: str = None
    nats_server: str = Field("127.0.0.1")
    nats_user: str = None
    nats_password: str = None
    log_level: str = Field("info")
    text: str = Field("[TG] {name}: {text}")
    sticker_string: str = Field("[STICKER]")
    video_string: str = Field("[MEDIA]")
    photo_string: str = Field("[PHOTO]")
    audio_string: str = Field("[AUDIO]")
    voice_string: str = Field("[VOICE]")
    reply_string: str = Field("[Reply {replay_id}] {msg}\n")
    repetition: int = Field(100)


class Msg(BaseModel):
    server_name: str | None = None
    name: str | None = None
    message_thread_id: str | None = None
    type: str | None
    text: str | None
