from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routes import trading_routes
from app.settings import settings
from app.trader import LiveTrading


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.trader = LiveTrading(
            api_key=settings.T_SANDBOX_TOKEN.get_secret_value(),
        )

        yield

    application = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)
    application.include_router(trading_routes.router)
    return application


app = create_app()
