from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    CRUD_API_URL: str = "http://localhost:8000" # URL de la API de Base de Datos

    class Config:
        env_file = ".env"

settings = Settings()
