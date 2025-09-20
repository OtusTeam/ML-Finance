import typing

from pydantic import BaseModel


class ExecuteTradeRequestBody(BaseModel):
    signal: typing.Literal["BUY", "SELL"]
    ticker: str
    trade_amount: int


class GetMarketDataRequestBody(BaseModel):
    ticker: str
    limit: int
