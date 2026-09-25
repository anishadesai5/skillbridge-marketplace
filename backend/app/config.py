from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./skillbridge.sqlite3"
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

settings = Settings()
