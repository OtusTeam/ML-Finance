import prometheus_client
from fastapi import APIRouter, Response, status
from fastapi.responses import JSONResponse


router = APIRouter(prefix="/trading")


@router.get("/metrics")
async def get_metrics() -> Response:
    return Response(content=prometheus_client.generate_latest(), media_type=prometheus_client.CONTENT_TYPE_LATEST)

@router.get("/healthcheck")
async def healthcheck() -> JSONResponse:
    return JSONResponse({"status": "ok"}, status_code=status.HTTP_200_OK)
