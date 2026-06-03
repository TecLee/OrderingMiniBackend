from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "OrderingMini API"
    DEBUG: bool = True
    DATABASE_URL: str = "sqlite:///./data/ordering.db"
    JWT_SECRET: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 72
    UPLOAD_DIR: str = "data/uploads"
    MOCK_AUTH: bool = True
    MOCK_VERIFY_CODE: str = "1234"
    DEEPSEEK_API_KEY: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
