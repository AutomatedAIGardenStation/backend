import pytest
import asyncio
from unittest.mock import MagicMock, patch
from app.services.serial_manager import SerialManager

@pytest.fixture
def mock_serial():
    with patch('app.services.serial_manager.serial.Serial') as mock:
        mock_instance = MagicMock()
        mock_instance.is_open = True
        mock_instance.in_waiting = 0
        mock_instance.readline.return_value = b""
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def config():
    return {"some_setting": "value"}

@pytest.mark.asyncio
async def test_connect_and_disconnect(mock_serial, config):
    manager = SerialManager(config)
    await manager.start()

    await manager.connect("test_controller", "/dev/ttyUSB0", 9600)
    assert "test_controller" in manager.connection_configs

    # Give the background task a moment to connect
    await asyncio.sleep(0.1)

    assert "test_controller" in manager.connections
    assert manager.connections["test_controller"] == mock_serial

    await manager.disconnect("test_controller")
    assert "test_controller" not in manager.connections
    mock_serial.close.assert_called_once()

    await manager.stop()

@pytest.mark.asyncio
async def test_queue_command_success(mock_serial, config):
    manager = SerialManager(config)
    await manager.start()

    await manager.connect("test_controller", "/dev/ttyUSB0")
    await asyncio.sleep(0.1)

    # Setup mock to return an ack shortly after
    async def simulate_ack():
        await asyncio.sleep(0.1)
        # Simulate incoming ack message
        await manager._process_incoming_message("test_controller", '{"ack": "test-cid", "status": "ok"}')

    asyncio.create_task(simulate_ack())

    # Send a command that requires an ACK
    result = await manager.queue_command(
        "test_controller",
        '{"cmd": "move"}',
        correlation_id="test-cid"
    )

    assert result == {"ack": "test-cid", "status": "ok"}
    mock_serial.write.assert_called_with(b'{"cmd": "move", "cid": "test-cid"}\n')

    await manager.stop()

@pytest.mark.asyncio
async def test_queue_command_timeout(mock_serial, config):
    manager = SerialManager(config)
    await manager.start()

    await manager.connect("test_controller", "/dev/ttyUSB0")
    await asyncio.sleep(0.1)

    # We will NOT send an ACK. It should timeout.
    with pytest.raises(TimeoutError):
        await manager.queue_command(
            "test_controller",
            '{"cmd": "move"}',
            timeout=0.2,
            retries=0,
            correlation_id="test-cid"
        )

    await manager.stop()

@pytest.mark.asyncio
async def test_safe_mode_transition(mock_serial, config):
    manager = SerialManager(config)
    await manager.start()

    await manager.connect("test_controller", "/dev/ttyUSB0")
    # Tweak timeout to be very short for the test
    manager.connection_configs["test_controller"].timeout = 0.2
    # Ensure last_heartbeats isn't updated by any reader loop by mocking it out or simply overwriting

    await asyncio.sleep(0.1)
    assert manager.safe_mode["test_controller"] is False

    # Force heartbeat to be old
    import time
    manager.last_heartbeats["test_controller"] = time.time() - 10.0

    # Wait for connection loop to cycle
    await asyncio.sleep(1.5)

    assert manager.safe_mode["test_controller"] is True

    # Attempting to send a command in safe mode should fail
    with pytest.raises(RuntimeError, match="is in safe mode"):
        await manager.queue_command("test_controller", '{"cmd": "test"}')
        # We need to yield to the queue loop so it processes the command and raises the exception on the future
        await asyncio.sleep(0.1)

    await manager.stop()

@pytest.mark.asyncio
async def test_read_event_parsing(mock_serial, config):
    manager = SerialManager(config)
    await manager.start()
    await manager.connect("test_controller", "/dev/ttyUSB0")

    await manager._process_incoming_message("test_controller", '{"event": "arm_done", "data": {"position": 100}}')

    event = await asyncio.wait_for(manager.get_next_event(), timeout=1.0)
    assert event["controller_id"] == "test_controller"
    assert event["event"] == "arm_done"
    assert event["data"] == {"position": 100}

    await manager.stop()
