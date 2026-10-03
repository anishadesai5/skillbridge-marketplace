from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./skillbridge.sqlite3"
    jwt_secret: str = "local-demo-secret-change-before-deployment"
    access_token_minutes: int = 60
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

settings = Settings()
