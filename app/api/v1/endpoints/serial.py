from fastapi import APIRouter, HTTPException, Depends
import asyncio
from app.schemas.serial import CommandRequest, ConnectionRequest
from app.services.serial_manager import SerialManager
from app.config import settings

router = APIRouter(prefix="/serial", tags=["serial"])

# For dependency injection, typically you'd inject from app state or a factory
# Here we'll instantiate a singleton for the router or assume it's attached to app state.
# Since app state isn't easily accessible without Request object, we'll create a module-level instance.
# In a real scenario, this would be initialized during FastAPI startup and attached to request.app.state.
# We'll expose a dependency to get it.

serial_manager_instance = SerialManager(config=settings.model_dump())

async def get_serial_manager() -> SerialManager:
    if not serial_manager_instance.is_running:
        await serial_manager_instance.start()
    return serial_manager_instance

@router.post("/connect", status_code=200)
async def connect_controller(
    request: ConnectionRequest,
    manager: SerialManager = Depends(get_serial_manager)
):
    try:
        await manager.connect(request.controller_id, request.port, request.baudrate)
        return {"status": "connected", "controller_id": request.controller_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/disconnect/{controller_id}", status_code=200)
async def disconnect_controller(
    controller_id: str,
    manager: SerialManager = Depends(get_serial_manager)
):
    await manager.disconnect(controller_id)
    return {"status": "disconnected", "controller_id": controller_id}

@router.post("/command")
async def send_command(
    request: CommandRequest,
    manager: SerialManager = Depends(get_serial_manager)
):
    try:
        response_data = await manager.queue_command(
            controller_id=request.controller_id,
            command=request.command,
            timeout=request.timeout,
            retries=request.retries,
            correlation_id=request.correlation_id
        )
        return response_data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except RuntimeError as e:
        # e.g., Safe mode
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events")
async def get_events(
    manager: SerialManager = Depends(get_serial_manager)
):
    """
    Returns the next event from the queue. Useful for long-polling.
    """
    try:
        # Wait up to 5 seconds for an event
        event = await asyncio.wait_for(manager.get_next_event(), timeout=5.0)
        return event
    except asyncio.TimeoutError:
        return {"status": "no_events"}
