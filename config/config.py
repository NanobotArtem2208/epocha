import os
from dotenv import load_dotenv
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv(override=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, env_file_encoding="utf-8"
    )

    APP_URL: str = "http://localhost:8000"
    STATIC_FOLDER: str = "web/static"
    LOGIN: SecretStr = SecretStr(os.getenv("LOGIN"))
    PASSWORD: SecretStr = SecretStr(os.getenv("PASSWORD"))
    
    
    
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_NAME: str = "postgres"
    DB_USER: str = "postgres"
    DB_PASS: str = "1"
    
    

settings = Settings()
