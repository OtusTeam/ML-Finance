import threading
import typing

from fastapi import APIRouter, Header, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel


router = APIRouter(prefix="/trading", tags=["Trading"])

idempotency_storage = set()
lock = threading.Lock()


class ExecuteTradeRequestBody(BaseModel):
    signal: typing.Literal["BUY", "SELL"]
    ticker: str
    trade_amount: int


@router.put("/add_funds")
async def add_funds(
    request: Request,
    amount: int = 100_000,
    idempotency_key: typing.Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> JSONResponse:
    if not idempotency_key:
        return JSONResponse(
            {"status": "error", "message": "Missing Idempotency-Key header"},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    with lock:
        if idempotency_key in idempotency_storage:
            return JSONResponse(
                {"status": "ok", "message": f"Duplicate request ignored (key={idempotency_key})"},
                status_code=status.HTTP_200_OK,
            )
        idempotency_storage.add(idempotency_key)

        request.app.trader.add_funds(amount=amount)
        return JSONResponse(
            {"status": "ok", "message": f"Funds added: {amount} (key={idempotency_key})"},
            status_code=status.HTTP_200_OK,
        )


@router.post("/execute_trade")
async def execute_trade(request: Request, request_body: ExecuteTradeRequestBody) -> JSONResponse:
    is_trade_executed = request.app.trader.execute_trade(
        signal=request_body.signal, ticker=request_body.ticker, trade_amount=request_body.trade_amount
    )
    if is_trade_executed:
        return JSONResponse({"status": "ok", "message": "Trade executed"}, status_code=status.HTTP_200_OK)
    return JSONResponse(
        {"status": "error", "message": "Trade execution failed"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


@router.delete("/delete_accounts")
async def delete_accounts(request: Request) -> JSONResponse:
    request.app.trader.close_sandbox_account()
    return JSONResponse({"status": "ok", "message": "All sandbox accounts deleted"}, status_code=status.HTTP_200_OK)
