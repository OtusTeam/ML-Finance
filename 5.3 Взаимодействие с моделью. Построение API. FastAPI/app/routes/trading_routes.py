import threading
from typing import Annotated

from fastapi import APIRouter, Header, Request, status
from fastapi.responses import JSONResponse


router = APIRouter(prefix="/trading", tags=["Trading"])

idempotency_storage = set()
lock = threading.Lock()


@router.put("/add_funds")
def add_funds(
    request: Request,
    amount: int = 100_000,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
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

        request.app.trader.add_funds(amount=amount)
        idempotency_storage.add(idempotency_key)

        return JSONResponse(
            {"status": "ok", "message": f"Funds added: {amount} (key={idempotency_key})"},
            status_code=status.HTTP_200_OK,
        )


@router.get("/start_trading")
def start_trading(request: Request):
    if request.app.trader.is_running:
        return JSONResponse(
            {"status": "error", "message": "Trading already running"}, status_code=status.HTTP_409_CONFLICT
        )

    def run():
        request.app.trader.start_live_trading(interval_seconds=60)

    if not hasattr(request.app, "trading_thread"):
        request.app.trading_thread = threading.Thread(target=run, daemon=True)
    request.app.trading_thread.start()
    return JSONResponse({"status": "ok", "message": "Trading started"}, status_code=status.HTTP_200_OK)


@router.get("/stop_trading")
def stop_trading(request: Request):
    if not request.app.trader.is_running:
        return JSONResponse(
            {"status": "error", "message": "Trading is not running"}, status_code=status.HTTP_409_CONFLICT
        )

    request.app.trader.is_running = False
    request.app.trading_thread.join()
    request.app.trading_thread = None
    return JSONResponse({"status": "ok", "message": "Trading stopped"}, status_code=status.HTTP_200_OK)


@router.delete("/delete_accounts")
def delete_accounts(request: Request):
    request.app.trader.close_sandbox_account()
    return JSONResponse({"status": "ok", "message": "All sandbox accounts deleted"}, status_code=status.HTTP_200_OK)
