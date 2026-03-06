import os
import pytest
from pydantic import ValidationError
from app.config import Settings

def test_settings_default_fallback():
    # If no env vars or config.yaml is found, it should use the defaults
    settings = Settings()
    assert settings.app_name == "Garden Station Backend"
    assert settings.environment == "development"
    assert settings.debug is False
    assert settings.secret_key == "default-unsafe-secret-key-change-in-production"

def test_settings_validation_error():
    # Test setting a too-short secret_key via environment variable
    os.environ["SECRET_KEY"] = "short"
    with pytest.raises(ValidationError) as excinfo:
        Settings()

    assert "String should have at least 32 characters" in str(excinfo.value)

    # Cleanup
    del os.environ["SECRET_KEY"]

def test_settings_env_override():
    os.environ["APP_NAME"] = "Test App Environment"
    os.environ["DEBUG"] = "true"

    settings = Settings()
    assert settings.app_name == "Test App Environment"
    assert settings.debug is True

    # Cleanup
    del os.environ["APP_NAME"]
    del os.environ["DEBUG"]
