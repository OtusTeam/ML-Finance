import uvicorn

from src.fastapi import app
from src.settings import settings


if __name__ == "__main__":
    uvicorn.run(app, host=settings.API_TRADER_HOST, port=settings.API_TRADER_PORT)
