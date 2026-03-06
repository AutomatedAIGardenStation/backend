import serial
import asyncio
from typing import Dict, Optional

class SerialManager:
    def __init__(self, config: Dict):
        self.connections = {}
        self.config = config

    async def connect(self, controller_id: str, port: str, baudrate: int = 9600):
        conn = serial.Serial(port, baudrate, timeout=1)
        self.connections[controller_id] = conn

    async def send_command(self, controller_id: str, command: str):
        conn = self.connections.get(controller_id)
        if conn is None:
            raise ConnectionError(f"No connection for {controller_id}")
        conn.write(f"{command}\n".encode())

    async def read_event(self, controller_id: str) -> Optional[str]:
        conn = self.connections.get(controller_id)
        if conn and conn.in_waiting:
            line = conn.readline().decode().strip()
            return line
        return None
