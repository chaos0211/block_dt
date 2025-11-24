# app/core/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 这个在 .env 里配置，不要写死在代码里
    SECRET_KEY: str = "super-secret-key-change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 365 * 5   # 1 天
    blockchain_difficulty: int = 4
    mining_reward: float = 10.0
    ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"


settings = Settings()