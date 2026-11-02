from pathlib import Path

from pydantic import Field, PositiveFloat, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class RabbitMQSettings(BaseSettings):
    """Load broker settings for the application and producer."""

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    rabbitmq_host: str = Field(default="localhost", min_length=1)
    rabbitmq_port: int = Field(default=5672, ge=1, le=65535)
    rabbitmq_user: str = Field(default="app", min_length=1)
    rabbitmq_password: SecretStr = SecretStr("app")
    rabbitmq_vhost: str = Field(default="/", min_length=1)
    rabbitmq_queue: str = Field(default="calls", min_length=1)
    rabbitmq_connect_timeout_seconds: PositiveFloat = 10


class Settings(RabbitMQSettings):
    """Extend broker settings with MongoDB configuration."""

    mongo_host: str = Field(default="localhost", min_length=1)
    mongo_port: int = Field(default=27017, ge=1, le=65535)
    mongo_user: str = Field(default="app", min_length=1)
    mongo_password: SecretStr = SecretStr("app")
    mongo_database: str = Field(default="kvint", min_length=1)
    mongo_auth_source: str = Field(default="admin", min_length=1)
    mongo_connect_timeout_seconds: PositiveFloat = 10
    mongo_operation_timeout_seconds: PositiveFloat = 10
    consumer_retry_delay_seconds: PositiveFloat = 3
    consumer_shutdown_timeout_seconds: PositiveFloat = 10
