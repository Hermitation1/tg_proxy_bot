from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str
    mtproxy_sources: list[str]
    proxies_sources: list[str]
    check_timeout: int = 3
    health_check_interval: int = 15

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
