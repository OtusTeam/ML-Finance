import threading
import typing

from fastapi import APIRouter, Header, Request, status
from fastapi.responses import JSONResponse

from app.models import ExecuteTradeRequestBody, GetMarketDataRequestBody


router = APIRouter(prefix="/trading", tags=["Trading"])

idempotency_storage = set()
lock = threading.Lock()


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
    trade_execution_result = request.app.trader.execute_trade(
        signal=request_body.signal, ticker=request_body.ticker, trade_amount=request_body.trade_amount
    )
    if trade_execution_result != -1:
        return JSONResponse({"status": "ok", "message": "Trade executed"}, status_code=status.HTTP_200_OK)
    return JSONResponse(
        {"status": "error", "message": "Trade execution failed"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


@router.delete("/delete_accounts")
async def delete_accounts(request: Request) -> JSONResponse:
    request.app.trader.close_sandbox_account()
    return JSONResponse({"status": "ok", "message": "All sandbox accounts deleted"}, status_code=status.HTTP_200_OK)


@router.post("/get_market_data")
async def get_market_data(request: Request, request_body: GetMarketDataRequestBody) -> JSONResponse:
    market_data = request.app.trader.get_market_data(ticker=request_body.ticker, limit=request_body.limit)
    if market_data[0].get("Error", False):
        return JSONResponse(
            {"status": "error", "message": f"Failed to fetch market data for {request_body.ticker}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return JSONResponse(
        {"status": "ok", "message": f"Fetched market data for {request_body.ticker}", "market_data": market_data},
        status_code=status.HTTP_200_OK,
    )
