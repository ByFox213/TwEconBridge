from pydantic import BaseModel, Field


class Env(BaseModel):
    message_thread_id: str = None
    server_name: str = Field("")
    nats_server: str = Field("127.0.0.1")
    nats_user: str = None
    nats_password: str = None
    econ_host: str = Field("127.0.0.1")
    econ_port: int = Field(8303)
    econ_password: str = Field("")
    auth_message: str = None
    log_level: str = Field("info")
    reconnection: bool = Field(False)
    reconnection_time: int = Field(5)
