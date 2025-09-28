import typing
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import pandas as pd
from tinkoff.invest import CandleInterval, Client, InstrumentStatus, MoneyValue, OrderDirection, OrderType
from tinkoff.invest.typedefs import AccountId
from tinkoff.invest.utils import decimal_to_quotation, now, quotation_to_decimal

from src.settings import LOGGER


class LiveTrading:
    """Класс для торговли в реальном времени."""

    def __init__(self, api_key: str) -> None:
        """Инициализация торговой стратегии.

        :param api_key: API ключ Т-инвестиций
        """
        self.api_key = api_key
        self.account_id = self._get_account_id()

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

    def get_market_data(self, ticker: str, limit: int = 100) -> list[dict[str, typing.Any]]:
        """Получение рыночных данных (свечей).

        :param ticker: Тикер инструмента
        :param limit: Кол-во свечей
        :return:
        """
        figi = self.get_figi_by_ticker(ticker)
        with Client(self.api_key) as api_client:
            candles_list = []
            try:
                for candle in api_client.get_all_candles(
                    figi=figi,
                    from_=now() - timedelta(minutes=limit + 5),  # Запас для точного кол-ва
                    to=now(),
                    interval=CandleInterval.CANDLE_INTERVAL_1_MIN,
                ):
                    candles_list.append(
                        {
                            "time": candle.time,
                            "open": float(quotation_to_decimal(candle.open)),
                            "high": float(quotation_to_decimal(candle.high)),
                            "low": float(quotation_to_decimal(candle.low)),
                            "close": float(quotation_to_decimal(candle.close)),
                            "volume": candle.volume,
                        }
                    )
                return pd.DataFrame(candles_list).set_index("time").tail(limit).to_dict(orient="records")
            except Exception as e:
                LOGGER.error(f"❌ Не удалось получить рыночные данные: {e}")
                return [{"Error": e}]

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

    def execute_trade(self, signal: str, ticker: str, trade_amount: int) -> int:
        """Выполнение торговой операции в песочнице.

        :param signal: Сигнал для покупки/продажи
        :param ticker: Тикер инструмента
        :param trade_amount: Количество лотов
        :return: 1, если операция исполнена; 0 если операцию не надо исполнять; -1, если ошибка при исполнении операции
        """
        figi = self.get_figi_by_ticker(ticker)

        with Client(self.api_key) as api_client:
            try:
                if signal == "BUY" and not self.current_position:
                    # Размещение рыночного ордера на покупку
                    order_response = api_client.sandbox.post_sandbox_order(
                        figi=figi,
                        quantity=trade_amount,
                        account_id=self.account_id,
                        direction=OrderDirection.ORDER_DIRECTION_BUY,
                        order_type=OrderType.ORDER_TYPE_MARKET,
                        order_id=str(uuid4()),
                    )

                    if order_response.execution_report_status == 1:  # Исполнен
                        self.current_position = "LONG"
                        LOGGER.info(
                            f"✅ ПОКУПКА ИСПОЛНЕНА: {trade_amount} {ticker} "
                            f"по цене ~{quotation_to_decimal(order_response.executed_order_price):.6f}"
                        )
                        return 1
                    LOGGER.error(f"❌ Ошибка выполнения покупки: {order_response.reject_reason}")
                    return -1

                if signal == "SELL" and self.current_position == "LONG":
                    # Размещение рыночного ордера на продажу
                    order_response = api_client.sandbox.post_sandbox_order(
                        figi=figi,
                        quantity=trade_amount,
                        account_id=self.account_id,
                        direction=OrderDirection.ORDER_DIRECTION_SELL,
                        order_type=OrderType.ORDER_TYPE_MARKET,
                        order_id=str(uuid4()),
                    )

                    if order_response.execution_report_status == 1:  # Исполнен
                        self.current_position = None
                        LOGGER.info(
                            f"✅ ПРОДАЖА ИСПОЛНЕНА: {trade_amount} {ticker} "
                            f"по цене ~{quotation_to_decimal(order_response.executed_order_price):.6f}"
                        )
                        return 1
                    LOGGER.error(f"❌ Ошибка выполнения продажи: {order_response.reject_reason}")
                    return -1
                return 0

            except Exception as e:
                LOGGER.error(f"❌ Ошибка выполнения торговой операции: {e}")
                return -1
