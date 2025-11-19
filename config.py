import os
from fastapi import HTTPException


class Settings:
    @property
    def openai_api_key(self) -> str:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")
        return key

    @property
    def openai_model(self) -> str:
        model = os.getenv("OPENAI_MODEL")
        if not model:
            raise HTTPException(status_code=500, detail="OPENAI_MODEL not configured")
        return model


settings = Settings()
