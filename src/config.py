from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://vidaxl:vidaxl@localhost:5432/vidaxl_footprint"
    ANTHROPIC_API_KEY: str = ""
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    @property
    def use_mock_analysis(self) -> bool:
        return not self.ANTHROPIC_API_KEY

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
