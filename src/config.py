from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://vidaxl:vidaxl@localhost:5432/vidaxl_footprint"
    ANTHROPIC_API_KEY: str = ""
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    USE_BEDROCK: bool = False
    AWS_REGION: str = "eu-central-1"
    BEDROCK_MODEL_ID: str = "eu.anthropic.claude-haiku-4-5-20251001-v1:0"
    TAVILY_API_KEY: str = ""
    API_KEY: str = ""
    AUTH_USERNAME: str = ""
    AUTH_PASSWORD: str = ""
    AUTH_SECRET: str = ""

    @property
    def use_mock_search(self) -> bool:
        return not self.TAVILY_API_KEY

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
