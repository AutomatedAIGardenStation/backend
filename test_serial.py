import asyncio
from app.services.serial_manager import SerialManager

async def main():
    manager = SerialManager({})
    print("Manager initialized")

asyncio.run(main())
