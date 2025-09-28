import uvicorn

from src.fastapi import app
from src.settings import settings


if __name__ == "__main__":
    uvicorn.run(app, host=settings.ML_SIGNALS_HOST, port=settings.ML_SIGNALS_PORT)
