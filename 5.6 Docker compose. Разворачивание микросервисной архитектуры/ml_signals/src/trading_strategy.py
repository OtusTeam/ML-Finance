import time
import typing
from datetime import datetime

import numpy as np
import pandas as pd
import requests
import torch
from chronos import ChronosPipeline

from src.metrics import app_metrics
from src.settings import LOGGER, settings


class LiveTradingStrategy:
    """Класс для торговли в реальном времени."""

    def __init__(self, ticker: str, trade_amount: int, pipeline: ChronosPipeline) -> None:
        """Инициализация торговой стратегии.

        :param ticker: Тикер инструмента, который будет торговаться
        :param trade_amount: Кол-во лотов для заявки
        :param pipeline: Пайплайн для ML модели
        """
        self.ticker = ticker
        self.trade_amount = trade_amount
        self.pipeline = pipeline

        self.is_running = False
        self.current_position = None
        self.last_signal = None

    def calculate_signals(self, data: pd.DataFrame) -> dict[str, typing.Any]:
        """Расчет торговых сигналов с помощью ML-модели.
        Эту функцию нужно адаптировать под вашу модель.

        :param data: DataFrame с ценами закрытия
        :return: Сигнал для покупки/продажи
        """
        if len(data) < 10:
            return {"signal": "HOLD", "reason": "Недостаточно данных"}

        calculating_signal_start_time = time.time()

        context = torch.tensor(data["close"].astype(float))
        prediction_length = 1
        LOGGER.debug("Forecasting...")

        model_prediction_start_time = time.time()
        forecast = self.pipeline.predict(context, prediction_length)
        app_metrics["ml_model_prediction_time"].labels(
            app_name=settings.APP_NAME,
            app_version=settings.APP_VERSION,
            model_name=settings.ML_MODEL_NAME,
            model_version=settings.ML_MODEL_VERSION,
        ).observe(time.time() - model_prediction_start_time)
        _, median, _ = np.quantile(forecast[0].numpy(), [0.1, 0.5, 0.9], axis=0)
        predicted_price = median[0]
        current_price = data["close"].iloc[-1]
        LOGGER.debug(f"Predicted price: {predicted_price},\nCurrent price: {current_price}")

        signal = "HOLD"
        reason = "Ожидание"
        if current_price < predicted_price:
            signal = "BUY"
            reason = "Текущая цена ниже предсказанной"

        elif current_price > predicted_price:
            signal = "SELL"
            reason = "Текущая цена выше предсказанной"

        app_metrics["calculating_signal_time"].labels(
            app_name=settings.APP_NAME,
            app_version=settings.APP_VERSION,
            model_name=settings.ML_MODEL_NAME,
            model_version=settings.ML_MODEL_VERSION,
        ).observe(time.time() - calculating_signal_start_time)

        app_metrics["signals_counter"].labels(
            app_name=settings.APP_NAME,
            app_version=settings.APP_VERSION,
            model_name=settings.ML_MODEL_NAME,
            model_version=settings.ML_MODEL_VERSION,
            signal=signal,
        ).inc()

        return {
            "signal": signal,
            "reason": reason,
            "current_price": current_price,
            "timestamp": data.index[-1],
        }

    def analyze_and_trade(self, market_data: list[dict[str, typing.Any]]) -> None:
        """Анализ рынка и выполнение торговых операций.

        :return: None
        """
        try:
            if market_data is None or len(market_data) == 0:
                LOGGER.error("❌ Не удалось получить рыночные данные.")
                return

            market_data = pd.DataFrame(market_data)

            analysis = self.calculate_signals(market_data)

            LOGGER.info(
                f"\n{'=' * 60}"
                f"\n📊 АНАЛИЗ РЫНКА - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                f"\n{'=' * 60}"
                f"\nСимвол: {self.ticker}"
                f"\nТекущая цена: {analysis['current_price']:.6f}"
                f"\nСигнал: {analysis['signal']}"
                f"\nПричина: {analysis['reason']}"
            )

            if analysis["signal"] in ["BUY", "SELL"] and analysis["signal"] != self.last_signal:
                LOGGER.info(f"🔔 НОВЫЙ ТОРГОВЫЙ СИГНАЛ: {analysis['signal']}")
                response = requests.post(
                    f"http://{settings.API_TRADER_HOST}:{settings.API_TRADER_PORT}/trading/execute_trade",
                    json={"signal": analysis["signal"], "ticker": self.ticker, "trade_amount": self.trade_amount},
                )
                if response.status_code != 200:
                    LOGGER.error("Signal execution failed")
                else:
                    LOGGER.info("Signal executed successfully")
        except Exception as e:
            LOGGER.error(f"❌ Ошибка в analyze_and_trade: {e}")

    def start_live_trading(self, interval_seconds: int = 60) -> None:
        """Запуск торговли в реальном времени.

        :param interval_seconds: Интервал анализа рынка и торговли
        :return: None
        """
        LOGGER.info(
            f"\n🚀 ЗАПУСК LIVE ТОРГОВЛИ\nИнтервал анализа: {interval_seconds} секунд\nДля остановки нажмите Ctrl+C"
        )

        self.is_running = True
        try:
            while self.is_running:
                total_order_execution_latency_start_time = time.time()
                LOGGER.info("Requesting market data...")
                response = requests.post(
                    f"http://{settings.API_TRADER_HOST}:{settings.API_TRADER_PORT}/trading/get_market_data",
                    json={"ticker": self.ticker, "limit": 50},
                )
                LOGGER.info(f"Got market data with {response.status_code} status code")
                market_data = None if response.status_code != 200 else response.json()["market_data"]
                self.analyze_and_trade(market_data)

                app_metrics["total_order_execution_latency_time"].labels(
                    app_name=settings.APP_NAME,
                    app_version=settings.APP_VERSION,
                    model_name=settings.ML_MODEL_NAME,
                    model_version=settings.ML_MODEL_VERSION,
                ).observe(time.time() - total_order_execution_latency_start_time)

                time.sleep(interval_seconds)
                LOGGER.debug("Waiting...")

        except KeyboardInterrupt:
            LOGGER.info("\n🛑 ОСТАНОВКА ТОРГОВЛИ")
            self.is_running = False
        except Exception as e:
            LOGGER.error(f"\n❌ Критическая ошибка: {e}")
            self.is_running = False
