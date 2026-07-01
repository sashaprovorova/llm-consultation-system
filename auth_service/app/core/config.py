from pydantic_settings import BaseSettings, SettingsConfigDict

# читаем настройки auth service из .env
class Settings(BaseSettings):
    app_name: str
    env: str

    jwt_secret: str
    jwt_alg: str
    access_token_expire_minutes: int

    sqlite_path: str

    model_config = SettingsConfigDict( env_file=".env", env_file_encoding="utf-8")


# общий объект настроек для всего сервиса
settings = Settings()