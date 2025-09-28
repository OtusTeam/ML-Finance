import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.metrics import app_metrics


class GetMetrics(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        req_time = time.time() - start
        app_metrics["request_time"].labels(
            app_name=request.app.title,
            app_version=request.app.version,
            req_url=request.url.path,
            method=request.method,
            http_status=response.status_code,
        ).observe(req_time)
        return response
