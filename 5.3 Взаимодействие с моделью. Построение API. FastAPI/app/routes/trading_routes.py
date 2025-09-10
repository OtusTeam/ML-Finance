import threading

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse


router = APIRouter(prefix="/trading", tags=["Trading"])


@router.post("/add_funds")
def add_funds(request: Request, amount: int = 100_000):
    request.app.trader.add_funds(amount=amount)
    return JSONResponse({"status": "ok", "message": f"Funds added: {amount}"}, status_code=status.HTTP_200_OK)


@router.get("/start_trading")
def start_trading(request: Request):
    if request.app.trader.is_running:
        return JSONResponse(
            {"status": "error", "message": "Trading already running"}, status_code=status.HTTP_409_CONFLICT
        )

    def run():
        request.app.trader.start_live_trading(interval_seconds=60)

    if not isinstance(request.app, threading.Thread):  # request.app.trading_thread:
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
