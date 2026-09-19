from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    log_level: str = "INFO"
    ethereum_rpc_url: str
    poll_interval_seconds: int = 60
    lookback_blocks: int = 500

    class Config:
        env_file = ".env"


settings = Settings()
