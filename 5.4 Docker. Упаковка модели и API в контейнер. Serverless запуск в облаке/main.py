import uvicorn

from app.fastapi import app
from app.settings import settings


if __name__ == "__main__":
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
