from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class CommandRequest(BaseModel):
    controller_id: str = Field(..., description="ID of the controller to send the command to")
    command: str = Field(..., description="JSON string or raw command to send")
    timeout: float = Field(5.0, description="Timeout in seconds for ACK")
    retries: int = Field(3, description="Number of retries on timeout")
    correlation_id: Optional[str] = Field(None, description="Optional custom correlation ID")

class CommandResponse(BaseModel):
    status: str = Field(..., description="Status of the command execution (e.g., 'ok', 'error')")
    data: Optional[Dict[str, Any]] = Field(None, description="Response payload from the controller")
    correlation_id: str = Field(..., description="Correlation ID matching the request")

class ConnectionRequest(BaseModel):
    controller_id: str = Field(..., description="ID of the controller")
    port: str = Field(..., description="Serial port (e.g., /dev/ttyUSB0)")
    baudrate: int = Field(9600, description="Baudrate")

class SerialEvent(BaseModel):
    controller_id: str = Field(..., description="ID of the controller emitting the event")
    event: str = Field(..., description="Event type (e.g., 'arm_done', 'fault')")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event payload")
    timestamp: float = Field(..., description="Unix timestamp of when the event was received")
