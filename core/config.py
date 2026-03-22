# core/config.py

from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    # jwt
    TOKEN_SECRET_KEY: str
    
    # database
    DATABASE_URL: str
    TEST_DATABASE_URL: str
    
    # google oauth
    GOOGLE_CLIENT_ID: str
    
    # ebay api
    EBAY_CLIENT_ID: str
    EBAY_CLIENT_SECRET: str

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

settings = Settings()