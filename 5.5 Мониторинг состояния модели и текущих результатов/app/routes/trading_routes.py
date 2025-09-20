import threading

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse


router = APIRouter(prefix="/trading", tags=["Trading"])

idempotency_storage = set()
lock = threading.Lock()


@router.get("/start_ml_analysis")
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


@router.get("/stop_ml_analysis")
def stop_trading(request: Request):
    if not request.app.trader.is_running:
        return JSONResponse(
            {"status": "error", "message": "Trading is not running"}, status_code=status.HTTP_409_CONFLICT
        )

    request.app.trader.is_running = False
    request.app.trading_thread.join()
    request.app.trading_thread = None
    return JSONResponse({"status": "ok", "message": "Trading stopped"}, status_code=status.HTTP_200_OK)
