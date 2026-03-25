from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://vidaxl:vidaxl@localhost:5432/vidaxl_footprint"
    ANTHROPIC_API_KEY: str = ""
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    USE_BEDROCK: bool = False
    AWS_REGION: str = "eu-central-1"
    BEDROCK_MODEL_ID: str = "eu.anthropic.claude-3-haiku-20240307-v1:0"
    API_KEY: str = ""
    AUTH_USERNAME: str = "levi9Hunkemoller"
    AUTH_PASSWORD: str = "Hunk3moll3r!"
    AUTH_SECRET: str = "change-me-in-production"

    @property
    def use_mock_analysis(self) -> bool:
        if self.USE_BEDROCK:
            return False
        return not self.ANTHROPIC_API_KEY

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
