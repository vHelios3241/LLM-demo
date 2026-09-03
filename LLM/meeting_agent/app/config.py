from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Database
    DB_URL: str = "sqlite://:memory:"

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"

    # Ali ASR
    ALI_ASR_API_KEY: str = ""
    ALI_ASR_APP_KEY: str = ""
    ALI_ASR_BASE_URL: str = ""

settings = Settings()
