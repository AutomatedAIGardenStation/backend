from datetime import datetime, timezone
from app.models.user import User, Role
from app.models.system import SystemConfig
from app.models.chamber import Chamber
from app.models.plant import Plant
from app.models.sensor import SensorReading
from app.models.actuator import ActuatorLog
from app.models.ml import MLPrediction
from app.models.harvest import HarvestQueue

def test_user_model_instantiation():
    user = User(username="test_user", email="test@example.com", hashed_password="hashed_pwd", role=Role.ADMIN)
    assert user.username == "test_user"
    assert user.email == "test@example.com"
    assert user.role == Role.ADMIN

def test_system_config_instantiation():
    config = SystemConfig(key="test_key", value="test_value")
    assert config.key == "test_key"
    assert config.value == "test_value"

def test_chamber_instantiation():
    chamber = Chamber(name="Chamber1", x=1.0, y=2.0, z=3.0)
    assert chamber.name == "Chamber1"
    assert chamber.x == 1.0
    assert chamber.y == 2.0
    assert chamber.z == 3.0

def test_plant_instantiation():
    now = datetime.now(timezone.utc)
    plant = Plant(chamber_id=1, species="Tomato", planted_at=now)
    assert plant.chamber_id == 1
    assert plant.species == "Tomato"
    assert plant.planted_at == now

def test_sensor_reading_instantiation():
    reading = SensorReading(plant_id=1, sensor_type="Temperature", value=22.5)
    assert reading.plant_id == 1
    assert reading.sensor_type == "Temperature"
    assert reading.value == 22.5

def test_actuator_log_instantiation():
    log = ActuatorLog(chamber_id=1, actuator_type="WaterPump", action="ON", parameters={"duration": 5})
    assert log.chamber_id == 1
    assert log.actuator_type == "WaterPump"
    assert log.action == "ON"
    assert log.parameters == {"duration": 5}

def test_ml_prediction_instantiation():
    prediction = MLPrediction(plant_id=1, prediction_type="Disease", confidence=0.95, result_data={"disease": "Blight"})
    assert prediction.plant_id == 1
    assert prediction.prediction_type == "Disease"
    assert prediction.confidence == 0.95
    assert prediction.result_data == {"disease": "Blight"}

def test_harvest_queue_instantiation():
    queue = HarvestQueue(plant_id=1, status="pending")
    assert queue.plant_id == 1
    assert queue.status == "pending"
