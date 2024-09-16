from typing import Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


settings = None


class GeneralSettings(BaseModel):
    instance_id: str


class AirflowSettings(BaseModel):
    host: str
    port: int
    login: str
    password: str


class BrokerSettings(BaseModel):
    host: str
    login: str
    password: str
    exchange: str
    queue_prefix: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='AIRBRIDGE__', env_nested_delimiter='__')

    general: GeneralSettings
    broker: BrokerSettings
    airflow: Optional[AirflowSettings] = Field(default=None)


def get_settings() -> Settings:
    global settings
    if settings is None:
        settings = Settings()
    return settings
