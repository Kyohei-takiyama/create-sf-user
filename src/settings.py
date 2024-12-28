import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SF_USER: str
    SF_PASSWORD: str
    SF_DOMAIN: str
    SF_TOKEN: str
    SF_API_BASE_URL: str

    class Config:
        env = os.getenv("ENV", "dev")
        env_file = f"src/envs/.env.{env}"
        case_sensitive = True