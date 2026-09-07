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

    # JWT
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30

settings = Settings()

# 启动期安全校验：未配置 JWT Secret 则拒绝启动
if not settings.JWT_SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY 未在 .env 中配置，出于安全考虑，应用拒绝启动！")
