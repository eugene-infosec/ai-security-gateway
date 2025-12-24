from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENV: str = "dev"
    LOG_LEVEL: str = "INFO"

    # Security / Auth Configuration
    AUTH_MODE: str = "jwt"  # Options: "jwt", "headers"
    ALLOW_INSECURE_HEADERS: bool = False

    # Pydantic V2: Use model_config instead of class Config
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

# Export variables to module level for easy import
# (e.g. `from app.settings import AUTH_MODE`)
ENV = settings.ENV
LOG_LEVEL = settings.LOG_LEVEL
AUTH_MODE = settings.AUTH_MODE
ALLOW_INSECURE_HEADERS = settings.ALLOW_INSECURE_HEADERS
