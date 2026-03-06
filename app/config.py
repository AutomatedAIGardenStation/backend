import logging
import yaml
from pathlib import Path
from typing import Tuple, Type, Any, Dict, List
from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

CONFIG_YAML_PATH = Path("app/config/config.yaml")

logger = logging.getLogger(__name__)


def _load_yaml_config() -> Dict[str, Any]:
    """Load and parse the YAML config file.

    Returns an empty dict if the file does not exist.
    Raises RuntimeError with a descriptive message if the file exists
    but cannot be read (e.g. permission denied) or parsed (e.g. syntax error),
    so that the application fails fast rather than starting with unsafe defaults.
    """
    if not CONFIG_YAML_PATH.exists():
        return {}
    try:
        with open(CONFIG_YAML_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except OSError as exc:
        raise RuntimeError(
            f"Configuration file '{CONFIG_YAML_PATH}' could not be read: {exc}"
        ) from exc
    except yaml.YAMLError as exc:
        raise RuntimeError(
            f"Configuration file '{CONFIG_YAML_PATH}' contains invalid YAML: {exc}"
        ) from exc


class YamlConfigSettingsSource(PydanticBaseSettingsSource):
    """
    A simple settings source that loads variables from a YAML file.
    """
    def get_field_value(
        self, field: Field, field_name: str
    ) -> Tuple[Any, str, bool]:
        yaml_data = _load_yaml_config()
        field_value = yaml_data.get(field_name)
        return field_value, field_name, False

    def prepare_field_value(
        self, field_name: str, field: Field, value: Any, value_is_complex: bool
    ) -> Any:
        return value

    def __call__(self) -> Dict[str, Any]:
        return _load_yaml_config()

class Settings(BaseSettings):
    app_name: str = "Garden Station Backend"
    environment: str = Field(default="development", description="Environment mode: development, staging, production")
    secret_key: str = Field(default="default-unsafe-secret-key-change-in-production", min_length=32, description="Secret key for application security")
    database_url: str = Field(default="sqlite+aiosqlite:///./test.db", description="Database connection URL")
    admin_emails: List[str] = Field(default_factory=list, description="List of administrator email addresses")
    debug: bool = Field(default=False, description="Enable debug mode")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            YamlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )

# Create a global instance of settings to be used throughout the app
settings = Settings()
