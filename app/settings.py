import os
from pydantic import BaseModel


class Settings(BaseModel):
    openai_api_key: str = os.getenv('OPENAI_API_KEY')
    openai_model: str = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    backend_api_base_url: str = os.getenv('BACKEND_API_BASE_URL', 'http://localhost:8000')


settings = Settings()
