from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    postgres_db: str
    postgres_user: str
    postgres_password: str
    db_host: str
    db_port: str
    secret_key: str
    encryption_algo: str

    model_config = SettingsConfigDict(env_file="../.env")
