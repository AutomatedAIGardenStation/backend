from fastapi import APIRouter

router = APIRouter(prefix="/sensors", tags=["sensors"])

@router.get("/{sensor_id}/latest")
async def get_latest_reading(sensor_id: str):
    return {"sensor_id": sensor_id, "reading": {}}
