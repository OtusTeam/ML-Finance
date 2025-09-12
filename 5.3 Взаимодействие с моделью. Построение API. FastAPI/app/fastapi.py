from contextlib import asynccontextmanager

import torch
from chronos import ChronosPipeline
from fastapi import FastAPI

from app.routes import trading_routes
from app.settings import LOGGER, settings
from app.trading_strategy import LiveTradingStrategy


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        try:
            LOGGER.info("Loading model...")
            pipeline = ChronosPipeline.from_pretrained(
                settings.ML_MODEL_PATH,
                local_files_only=True,
                device_map=settings.DEVICE,
                dtype=torch.bfloat16,
            )
            LOGGER.info("Model loaded")
        except Exception as e:
            LOGGER.error(f"Error during model loading: {e}")
            raise

        app.trader = LiveTradingStrategy(
            api_key=settings.T_SANDBOX_TOKEN.get_secret_value(),
            ticker=settings.TICKER,
            trade_amount=settings.TRADE_AMOUNT,
            pipeline=pipeline,
        )

        yield

    application = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)
    application.include_router(trading_routes.router)
    return application


app = create_app()
