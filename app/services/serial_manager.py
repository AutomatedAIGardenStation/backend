import serial
import asyncio
from typing import Dict, Optional, Any
import logging
import time
import uuid
import json

logger = logging.getLogger(__name__)

class ConnectionConfig:
    def __init__(self, port: str, baudrate: int = 9600, heartbeat_interval: float = 5.0, timeout: float = 10.0):
        self.port = port
        self.baudrate = baudrate
        self.heartbeat_interval = heartbeat_interval
        self.timeout = timeout

class CommandQueueItem:
    def __init__(self, command: str, correlation_id: str, timeout: float = 5.0, retries: int = 3):
        self.command = command
        self.correlation_id = correlation_id
        self.timeout = timeout
        self.max_retries = retries
        self.retries = 0
        self.future = asyncio.Future()
        self.sent_time = 0.0

class SerialManager:
    def __init__(self, config: Dict):
        self.connections: Dict[str, serial.Serial] = {}
        self.connection_configs: Dict[str, ConnectionConfig] = {}
        self.config = config

        self.is_running = False
        self.connection_tasks: Dict[str, asyncio.Task] = {}
        self.reader_tasks: Dict[str, asyncio.Task] = {}
        self.queue_tasks: Dict[str, asyncio.Task] = {}

        self.last_heartbeats: Dict[str, float] = {}
        self.last_sent_heartbeat: Dict[str, float] = {}
        self.safe_mode: Dict[str, bool] = {}

        self.command_queues: Dict[str, asyncio.Queue] = {}
        self.pending_commands: Dict[str, Dict[str, CommandQueueItem]] = {}
        self.events_queue: asyncio.Queue = asyncio.Queue()

    async def start(self):
        self.is_running = True
        logger.info("SerialManager started")

    async def stop(self):
        self.is_running = False
        logger.info("SerialManager stopping...")
        for controller_id in list(self.connections.keys()):
            await self.disconnect(controller_id)

        for task in self.connection_tasks.values():
            task.cancel()
        for task in self.reader_tasks.values():
            task.cancel()
        for task in self.queue_tasks.values():
            task.cancel()

    async def register_controller(self, controller_id: str, port: str, baudrate: int = 9600):
        self.connection_configs[controller_id] = ConnectionConfig(port, baudrate)
        self.safe_mode[controller_id] = False
        self.last_heartbeats[controller_id] = time.time()
        self.last_sent_heartbeat[controller_id] = 0.0

        self.command_queues[controller_id] = asyncio.Queue()
        self.pending_commands[controller_id] = {}

        # Start tasks
        self.connection_tasks[controller_id] = asyncio.create_task(self._connection_loop(controller_id))
        self.reader_tasks[controller_id] = asyncio.create_task(self._reader_loop(controller_id))
        self.queue_tasks[controller_id] = asyncio.create_task(self._queue_loop(controller_id))

    async def _connection_loop(self, controller_id: str):
        cfg = self.connection_configs[controller_id]

        while self.is_running:
            if controller_id not in self.connections or not self.connections[controller_id].is_open:
                try:
                    await self._connect_internal(controller_id, cfg.port, cfg.baudrate)
                    self.safe_mode[controller_id] = False
                    self.last_heartbeats[controller_id] = time.time()
                except Exception as e:
                    logger.warning(f"Reconnect failed for {controller_id}: {e}")
            else:
                now = time.time()
                # Check watchdog/heartbeat
                if now - self.last_heartbeats.get(controller_id, now) > cfg.timeout:
                    if not self.safe_mode.get(controller_id, False):
                        logger.error(f"Watchdog timeout for {controller_id}. Entering safe mode.")
                        self.safe_mode[controller_id] = True
                    # Disconnect to trigger reconnect
                    await self._disconnect_internal(controller_id)
                elif now - self.last_sent_heartbeat.get(controller_id, 0) > cfg.heartbeat_interval:
                    # Send heartbeat
                    try:
                        self.last_sent_heartbeat[controller_id] = now
                        await self.queue_command(controller_id, '{"cmd":"ping"}', timeout=2.0, retries=0)
                    except Exception as e:
                        logger.debug(f"Failed to queue heartbeat for {controller_id}: {e}")

            await asyncio.sleep(1.0)

    async def _reader_loop(self, controller_id: str):
        while self.is_running:
            conn = self.connections.get(controller_id)
            if conn and conn.is_open:
                try:
                    # Block on reading
                    def _read() -> Optional[str]:
                        if conn.in_waiting:
                            return conn.readline().decode().strip()
                        return None

                    line = await asyncio.to_thread(_read)
                    if line:
                        logger.debug(f"Read from {controller_id}: {line}")
                        self.last_heartbeats[controller_id] = time.time()
                        await self._process_incoming_message(controller_id, line)
                    else:
                        await asyncio.sleep(0.01)
                except Exception as e:
                    logger.error(f"Reader error for {controller_id}: {e}")
                    await asyncio.sleep(1.0)
            else:
                await asyncio.sleep(1.0)

    async def _queue_loop(self, controller_id: str):
        queue = self.command_queues[controller_id]
        pending = self.pending_commands[controller_id]

        while self.is_running:
            # Check timeouts for pending commands
            now = time.time()
            to_remove = []
            to_retry = []

            for cid, item in pending.items():
                if now - item.sent_time > item.timeout:
                    if item.retries < item.max_retries:
                        item.retries += 1
                        to_retry.append(item)
                    else:
                        if not item.future.done():
                            item.future.set_exception(TimeoutError(f"Command timeout after {item.max_retries} retries"))
                        to_remove.append(cid)

            for cid in to_remove:
                del pending[cid]

            for item in to_retry:
                # Re-send immediately
                try:
                    await self._send_raw(controller_id, item.command)
                    item.sent_time = time.time()
                    logger.warning(f"Retrying command {item.correlation_id} to {controller_id}")
                except Exception:
                    pass

            try:
                # Get next command
                item: CommandQueueItem = await asyncio.wait_for(queue.get(), timeout=0.5)

                if self.safe_mode.get(controller_id, False):
                    if not item.future.done():
                        item.future.set_exception(RuntimeError(f"Controller {controller_id} is in safe mode"))
                    continue

                pending[item.correlation_id] = item
                item.sent_time = time.time()

                try:
                    await self._send_raw(controller_id, item.command)
                except Exception as e:
                    if not item.future.done():
                        item.future.set_exception(e)
                    del pending[item.correlation_id]

            except asyncio.TimeoutError:
                pass

    async def _process_incoming_message(self, controller_id: str, message: str):
        # We expect JSON messages like {"ack": "cid", "status": "ok"} or {"event": "arm_done", "data": {}}
        try:
            data = json.loads(message)
            if "ack" in data:
                cid = str(data["ack"])
                pending = self.pending_commands.get(controller_id, {})
                if cid in pending:
                    item = pending.pop(cid)
                    if not item.future.done():
                        item.future.set_result(data)
            elif "event" in data:
                event_data = {
                    "controller_id": controller_id,
                    "event": data["event"],
                    "data": data.get("data", {}),
                    "timestamp": time.time()
                }
                await self.events_queue.put(event_data)
        except json.JSONDecodeError:
            # Non-JSON event, just wrap it
            event_data = {
                "controller_id": controller_id,
                "event": "raw",
                "data": {"raw_message": message},
                "timestamp": time.time()
            }
            await self.events_queue.put(event_data)

    async def _send_raw(self, controller_id: str, command: str):
        conn = self.connections.get(controller_id)
        if conn is None or not conn.is_open:
            raise ConnectionError(f"No connection for {controller_id}")

        await asyncio.to_thread(conn.write, f"{command}\n".encode())
        logger.debug(f"Sent to {controller_id}: {command}")

    async def queue_command(self, controller_id: str, command: str, timeout: float = 5.0, retries: int = 3, correlation_id: Optional[str] = None) -> Any:
        if controller_id not in self.command_queues:
            raise ValueError(f"Unknown controller {controller_id}")

        cid = correlation_id or str(uuid.uuid4())

        # Inject correlation_id if command is JSON and missing it
        try:
            data = json.loads(command)
            if "cid" not in data:
                data["cid"] = cid
                command = json.dumps(data)
            else:
                cid = data["cid"]
        except json.JSONDecodeError:
            pass

        item = CommandQueueItem(command, cid, timeout, retries)
        await self.command_queues[controller_id].put(item)

        return await item.future

    async def get_next_event(self) -> Dict[str, Any]:
        return await self.events_queue.get()

    async def _connect_internal(self, controller_id: str, port: str, baudrate: int = 9600):
        conn = await asyncio.to_thread(serial.Serial, port, baudrate, timeout=1)
        self.connections[controller_id] = conn
        logger.info(f"Connected to {controller_id} on {port} at {baudrate} baud")

    async def connect(self, controller_id: str, port: str, baudrate: int = 9600):
        await self.register_controller(controller_id, port, baudrate)

    async def _disconnect_internal(self, controller_id: str):
        conn = self.connections.pop(controller_id, None)
        if conn and conn.is_open:
            try:
                await asyncio.to_thread(conn.close)
                logger.info(f"Disconnected from {controller_id}")
            except Exception as e:
                logger.error(f"Error disconnecting from {controller_id}: {e}")

    async def disconnect(self, controller_id: str):
        if controller_id in self.connection_tasks:
            self.connection_tasks[controller_id].cancel()
        if controller_id in self.reader_tasks:
            self.reader_tasks[controller_id].cancel()
        if controller_id in self.queue_tasks:
            self.queue_tasks[controller_id].cancel()
        await self._disconnect_internal(controller_id)

    async def send_command(self, controller_id: str, command: str):
        # Kept for backward compatibility, bypasses queue
        if self.safe_mode.get(controller_id, False):
            raise RuntimeError(f"Cannot send command. {controller_id} is in safe mode.")
        await self._send_raw(controller_id, command)

    async def read_event(self, controller_id: str) -> Optional[str]:
        # Kept for backward compatibility, though events are now pushed to queue
        return None
