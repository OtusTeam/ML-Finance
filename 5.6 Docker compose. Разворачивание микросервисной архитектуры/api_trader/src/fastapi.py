from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.routes import service_routes, trading_routes
from src.settings import settings
from src.trader import LiveTrading
from src.middlewares import GetMetrics

def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.trader = LiveTrading(
            api_key=settings.T_SANDBOX_TOKEN.get_secret_value(),
        )

        yield

    application = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)
    application.include_router(trading_routes.router)
    application.include_router(service_routes.router)
    application.add_middleware(GetMetrics)
    return application


app = create_app()
