import time
import typing
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import numpy as np
import pandas as pd
import torch
from chronos import ChronosPipeline
from tinkoff.invest import CandleInterval, Client, InstrumentStatus, MoneyValue, OrderDirection, OrderType
from tinkoff.invest.typedefs import AccountId
from tinkoff.invest.utils import decimal_to_quotation, now, quotation_to_decimal

from settings import LOGGER


class LiveTradingStrategy:
    """Класс для торговли в реальном времени."""

    def __init__(self, api_key: str, ticker: str, trade_amount: int, pipeline: ChronosPipeline) -> None:
        """Инициализация торговой стратегии.

        :param api_key: API ключ Т-инвестиций
        :param ticker: Тикер инструмента, который будет торговаться
        :param trade_amount: Кол-во лотов для заявки
        :param pipeline: Пайплайн для ML модели
        """
        self.api_key = api_key
        self.ticker = ticker
        self.trade_amount = trade_amount
        self.account_id = self._get_account_id()
        self.figi = self.get_figi_by_ticker(self.ticker)
        self.pipeline = pipeline

        self.is_running = False
        self.current_position = None
        self.last_signal = None

    def _get_account_id(self) -> AccountId:
        """Получение ID брокерского счёта.

        :return: ID брокерского счёта
        """
        with Client(self.api_key) as api_client:
            response = api_client.sandbox.get_sandbox_accounts()
            if not response.accounts:
                # Если счетов нет, создаем новый
                new_account = api_client.sandbox.open_sandbox_account()
                return new_account.account_id
            # Для простоты берем первый аккаунт, в реальных условиях лучше выбрать нужный.
            return response.accounts[0].id

    def close_sandbox_account(self) -> None:
        """Закрытие всех счетов в песочнице для чистого запуска.

        :return: None
        """
        with Client(self.api_key) as api_client:
            accounts = api_client.sandbox.get_sandbox_accounts().accounts
            for account in accounts:
                api_client.sandbox.close_sandbox_account(account_id=account.id)
            LOGGER.info("Все старые аккаунты песочницы закрыты.")

    def _download_instruments_list(self) -> None:
        """Загрузка списка акций и заполнение маппера ticker-figi.
        :return: None.
        """
        with Client(self.api_key) as api_client:
            shares_df = pd.DataFrame(
                api_client.instruments.shares(instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE).instruments
            )
            self.shares = shares_df[shares_df["currency"] == "rub"].reset_index(drop=True)[
                ["figi", "ticker", "class_code", "first_1min_candle_date", "currency", "name"]
            ]
            self.tickers_figi_mapper = self.shares.set_index("ticker")["figi"].to_dict()
            self.figi_tickers_mapper = {one_value: one_key for one_key, one_value in self.tickers_figi_mapper.items()}

    def get_figi_by_ticker(self, ticker: str) -> str:
        """Получение FIGI по тикеру. Если маппер пустой, загружаем инструменты.

        :param ticker: Тикер торгового инструмента
        :return: FIGI торгового инструмента
        """
        if not hasattr(self, "tickers_figi_mapper") or not self.tickers_figi_mapper:
            self._download_instruments_list()
        figi = self.tickers_figi_mapper.get(ticker)
        if not figi:
            raise ValueError(f"FIGI для тикера '{ticker}' не найден.")
        return figi

    def get_historic_day_candles_by_ticker(self, ticker: str, delta_days: int) -> pd.DataFrame:
        """Получение исторических дневных свечей по тикеру.

        :param ticker: Тикер торгового инструмента
        :param delta_days: Количество дней для загрузки
        :return: DataFrame с историческими свечами
        """
        figi = self.get_figi_by_ticker(ticker)
        with Client(self.api_key) as api_client:
            candles_list = []
            for candle in api_client.get_all_candles(
                figi=figi,
                from_=now() - timedelta(days=delta_days),
                to=now(),
                interval=CandleInterval.CANDLE_INTERVAL_DAY,
            ):
                LOGGER.info(f"DATA {candle.open}, {type(candle.open)}")
                candles_list.append(
                    {
                        "time": candle.time,
                        "open": quotation_to_decimal(candle.open),
                        "high": quotation_to_decimal(candle.high),
                        "low": quotation_to_decimal(candle.low),
                        "close": quotation_to_decimal(candle.close),
                        "volume": candle.volume,
                    }
                )
            return pd.DataFrame(candles_list).set_index("time")

    def add_funds(self, amount: int, currency: str = "rub") -> None:
        """Пополнение брокерского счёта в песочнице.

        :param amount: Сумма пополнения
        :param currency: Валюта
        :return: None
        """
        money = decimal_to_quotation(Decimal(amount))
        with Client(self.api_key) as api_client:
            api_client.sandbox.sandbox_pay_in(
                account_id=self.account_id, amount=MoneyValue(units=money.units, nano=money.nano, currency=currency)
            )
            LOGGER.info(f"Баланс песочницы пополнен на {amount} RUB.")

    def cancel_all_orders(self) -> None:
        """Отменить все активные заявки.

        :return: None
        """
        with Client(self.api_key) as api_client:
            LOGGER.info(f"Заявки: {api_client.sandbox.get_sandbox_orders(account_id=self.account_id)}")
            LOGGER.info("Отмена всех заявок...")
            api_client.cancel_all_orders(account_id=self.account_id)
            LOGGER.info("Все заявки отменены")
            LOGGER.info(f"Заявки: {api_client.sandbox.get_sandbox_orders(account_id=self.account_id)}")

    def get_market_data(self, limit: int = 100) -> pd.DataFrame | None:
        """Получение рыночных данных (свечей).

        :param limit:
        :return:
        """
        with Client(self.api_key) as api_client:
            candles_list = []
            try:
                for candle in api_client.get_all_candles(
                    figi=self.figi,
                    from_=now() - timedelta(minutes=limit + 5),  # Запас для точного кол-ва
                    to=now(),
                    interval=CandleInterval.CANDLE_INTERVAL_1_MIN,
                ):
                    candles_list.append(
                        {
                            "time": candle.time,
                            "open": quotation_to_decimal(candle.open),
                            "high": quotation_to_decimal(candle.high),
                            "low": quotation_to_decimal(candle.low),
                            "close": quotation_to_decimal(candle.close),
                            "volume": candle.volume,
                        }
                    )
                return pd.DataFrame(candles_list).set_index("time").tail(limit)
            except Exception as e:
                LOGGER.error(f"❌ Не удалось получить рыночные данные: {e}")
                return None

    def calculate_signals(self, data: pd.DataFrame) -> dict[str, typing.Any]:
        """Расчет торговых сигналов с помощью ML-модели.
        Эту функцию нужно адаптировать под вашу модель.

        :param data: DataFrame с ценами закрытия
        :return: Сигнал для покупки/продажи
        """
        if len(data) < 10:
            return {"signal": "HOLD", "reason": "Недостаточно данных"}

        context = torch.tensor(data["close"].astype(float))
        prediction_length = 1
        LOGGER.debug("Forecasting...")
        forecast = self.pipeline.predict(context, prediction_length)
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

        return {
            "signal": signal,
            "reason": reason,
            "current_price": current_price,
            "timestamp": data.index[-1],
        }

    def get_account_status(self) -> dict[str, typing.Any]:
        """Получение статуса аккаунта: баланс и позиции.

        :return: Статус аккаунта: баланс и позиции
        """
        with Client(self.api_key) as api_client:
            try:
                balance = float(
                    quotation_to_decimal(api_client.sandbox.get_sandbox_positions(account_id=self.account_id).money[0])
                )
                positions = api_client.sandbox.get_sandbox_positions(account_id=self.account_id)
                open_orders = api_client.sandbox.get_sandbox_orders(account_id=self.account_id)

                return {"balance": balance, "positions": positions.securities, "open_orders": open_orders.orders}
            except Exception as e:
                LOGGER.error(f"❌ Ошибка при получении статуса аккаунта: {e}")
                return {"balance": None, "positions": [], "open_orders": []}

    def execute_trade(self, signal: str, current_price: float) -> bool:
        """Выполнение торговой операции в песочнице.
        Используется `orders.post_order` с токеном песочницы.

        :param signal: Сигнал для покупки/продажи
        :param current_price: Текущая цена инструмента
        :return: True, если операция исполнена; False, если операция не исполнена
        """
        with Client(self.api_key) as api_client:
            try:
                if signal == "BUY" and not self.current_position:
                    # Размещение рыночного ордера на покупку
                    order_response = api_client.sandbox.post_sandbox_order(
                        figi=self.figi,
                        quantity=self.trade_amount,
                        account_id=self.account_id,
                        direction=OrderDirection.ORDER_DIRECTION_BUY,
                        order_type=OrderType.ORDER_TYPE_MARKET,
                        order_id=str(uuid4()),
                    )

                    if order_response.execution_report_status == 1:  # Исполнен
                        self.current_position = "LONG"
                        LOGGER.info(
                            f"✅ ПОКУПКА ИСПОЛНЕНА: {self.trade_amount} {self.ticker} по цене ~{current_price:.6f}"
                        )
                        return True
                    LOGGER.error(f"❌ Ошибка выполнения покупки: {order_response.reject_reason}")
                    return False

                if signal == "SELL" and self.current_position == "LONG":
                    # Размещение рыночного ордера на продажу
                    order_response = api_client.sandbox.post_sandbox_order(
                        figi=self.figi,
                        quantity=self.trade_amount,
                        account_id=self.account_id,
                        direction=OrderDirection.ORDER_DIRECTION_SELL,
                        order_type=OrderType.ORDER_TYPE_MARKET,
                        order_id=str(uuid4()),
                    )

                    if order_response.execution_report_status == 1:  # Исполнен
                        self.current_position = None
                        LOGGER.info(
                            f"✅ ПРОДАЖА ИСПОЛНЕНА: {self.trade_amount} {self.ticker} по цене ~{current_price:.6f}"
                        )
                        return True
                    LOGGER.error(f"❌ Ошибка выполнения продажи: {order_response.reject_reason}")
                    return False

                return False

            except Exception as e:
                LOGGER.error(f"❌ Ошибка выполнения торговой операции: {e}")
                return False

    def analyze_and_trade(self) -> None:
        """Анализ рынка и выполнение торговых операций.

        :return: None
        """
        try:
            data = self.get_market_data(limit=50)  # Получаем 50 свечей
            if data is None or len(data) == 0:
                LOGGER.error("❌ Не удалось получить рыночные данные.")
                return

            analysis = self.calculate_signals(data)
            account_status = self.get_account_status()

            LOGGER.info(
                f"\n{'=' * 60}"
                f"\n📊 АНАЛИЗ РЫНКА - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                f"\n{'=' * 60}"
                f"\nСимвол: {self.ticker}"
                f"\nТекущая цена: {analysis['current_price']:.6f}"
                f"\nСигнал: {analysis['signal']}"
                f"\nПричина: {analysis['reason']}"
                f"\nТекущая позиция: {self.current_position or 'НЕТ'}"
            )

            if analysis["signal"] in ["BUY", "SELL"] and analysis["signal"] != self.last_signal:
                LOGGER.info(f"🔔 НОВЫЙ ТОРГОВЫЙ СИГНАЛ: {analysis['signal']}")
                if self.execute_trade(analysis["signal"], analysis["current_price"]):
                    self.last_signal = analysis["signal"]
                    time.sleep(2)
                    account_status = self.get_account_status()

            if account_status["balance"]:
                LOGGER.info(f"💰 СТАТУС АККАУНТА:\nБаланс: {account_status['balance']}")

            if account_status["positions"]:
                LOGGER.info(f"\n📈 ТЕКУЩИЕ ПОЗИЦИИ: {len(account_status['positions'])}")
                for pos in account_status["positions"]:
                    LOGGER.info(f"{pos.figi} ({self.figi_tickers_mapper.get(pos.figi, "")}): {pos.balance} (в лотах)")

            if account_status["open_orders"]:
                LOGGER.info(f"\n📋 ОТКРЫТЫЕ ОРДЕРА: {len(account_status['open_orders'])}")

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

        LOGGER.info("Получение ID аккаунта и FIGI...")
        try:
            self.account_id = self._get_account_id()
            self.figi = self.get_figi_by_ticker(self.ticker)
            LOGGER.info(f"ID аккаунта: {self.account_id}")
            LOGGER.info(f"FIGI для {self.ticker}: {self.figi}")
        except Exception as e:
            LOGGER.error(f"❌ Критическая ошибка при инициализации: {e}")
            return

        self.is_running = True
        try:
            while self.is_running:
                self.analyze_and_trade()
                time.sleep(interval_seconds)
                LOGGER.debug("Waiting...")

        except KeyboardInterrupt:
            LOGGER.info("\n🛑 ОСТАНОВКА ТОРГОВЛИ")
            self.is_running = False
        except Exception as e:
            LOGGER.error(f"\n❌ Критическая ошибка: {e}")
            self.is_running = False
