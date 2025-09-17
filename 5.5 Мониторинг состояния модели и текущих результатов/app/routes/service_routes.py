import prometheus_client
from fastapi import APIRouter, Response


router = APIRouter(tags=["Service"])


@router.get("/metrics")
async def get_metrics() -> Response:
    return Response(content=prometheus_client.generate_latest(), media_type=prometheus_client.CONTENT_TYPE_LATEST)
