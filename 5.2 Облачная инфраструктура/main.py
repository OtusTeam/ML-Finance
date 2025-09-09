import logging
import os

import torch
import typer
from chronos import ChronosPipeline
from dotenv import load_dotenv

from api_client import LiveTradingStrategy


load_dotenv()
logging.basicConfig(level=logging.INFO)

pipeline = ChronosPipeline.from_pretrained(
    "chronos-t5-tiny/",
    local_files_only=True,
    device_map="cpu",
    dtype=torch.bfloat16,
)

app = typer.Typer(help="Торговый бот для Tinkoff Invest API в песочнице.")


@app.command(help="Запускает торговую стратегию в режиме реального времени.")
def start_trading():
    trading_strategy = LiveTradingStrategy(
        api_key=os.getenv("T_SANDBOX_TOKEN"), ticker="SBER", trade_amount=1, pipeline=pipeline
    )
    trading_strategy.start_live_trading()


@app.command(help="Добавляет средства на счёт песочницы")
def add_funds(amount: int = typer.Option(100_000, help="Cумма для пополнения счета в песочнице.")):
    trading_strategy = LiveTradingStrategy(
        api_key=os.getenv("T_SANDBOX_TOKEN"), ticker="SBER", trade_amount=1, pipeline=pipeline
    )
    trading_strategy.add_funds(amount=amount)


@app.command(help="Удаляет все аккаунты песочницы, чтобы начать с чистого листа.")
def delete_accounts():
    trading_strategy = LiveTradingStrategy(
        api_key=os.getenv("T_SANDBOX_TOKEN"), ticker="SBER", trade_amount=1, pipeline=pipeline
    )
    trading_strategy.close_sandbox_account()


if __name__ == "__main__":
    app()
