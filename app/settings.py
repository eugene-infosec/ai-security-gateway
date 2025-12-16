from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENV: str = "dev"
    LOG_LEVEL: str = "INFO"

    # Pydantic V2: Use model_config instead of class Config
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
