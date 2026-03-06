import os
import pytest
from unittest.mock import patch
from pydantic import ValidationError
from app.config import Settings, _load_yaml_config

def test_settings_default_fallback(monkeypatch, tmp_path):
    # Point CONFIG_YAML_PATH to a non-existent path to truly test fallback behavior
    monkeypatch.setattr(app.config, "CONFIG_YAML_PATH", tmp_path / "nonexistent.yaml")
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


def test_yaml_config_raises_on_os_error(tmp_path, monkeypatch):
    """_load_yaml_config raises RuntimeError (not silently returns {}) when the
    YAML file exists but cannot be opened due to an OS-level error."""
    import app.config as config_module

    fake_path = tmp_path / "config.yaml"
    fake_path.write_text("app_name: test")
    monkeypatch.setattr(config_module, "CONFIG_YAML_PATH", fake_path)

    with patch("builtins.open", side_effect=OSError("permission denied")):
        with pytest.raises(RuntimeError, match="could not be read"):
            _load_yaml_config()


def test_yaml_config_raises_on_invalid_yaml(tmp_path, monkeypatch):
    """_load_yaml_config raises RuntimeError (not silently returns {}) when the
    YAML file exists but contains invalid YAML syntax."""
    import app.config as config_module

    fake_path = tmp_path / "config.yaml"
    fake_path.write_text(": bad: yaml: [unclosed")
    monkeypatch.setattr(config_module, "CONFIG_YAML_PATH", fake_path)

    with pytest.raises(RuntimeError, match="invalid YAML"):
        _load_yaml_config()


def test_yaml_config_returns_empty_when_file_absent(tmp_path, monkeypatch):
    """_load_yaml_config returns {} without raising when the file does not exist."""
    import app.config as config_module

    monkeypatch.setattr(config_module, "CONFIG_YAML_PATH", tmp_path / "nonexistent.yaml")

    result = _load_yaml_config()
    assert result == {}
