import os
from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "CUBE Receiving Manager API"
    version: str = "1.0.0"
    api_prefix: str = "/api/v1"
    vision_provider: str = os.getenv("VISION_PROVIDER", "mock").lower()
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://cube-rcv-frontend.onrender.com",
    ]


settings = Settings()
