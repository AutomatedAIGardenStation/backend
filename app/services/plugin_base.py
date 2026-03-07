import abc
from typing import Any, Dict

class PluginBase(abc.ABC):
    """
    Abstract base class defining the core async lifecycle traits for all plugins.
    Plugins must implement these methods to be loaded and managed safely.
    """

    @abc.abstractmethod
    async def init(self, config: Dict[str, Any]) -> None:
        """
        Initialize the plugin with the provided configuration.
        """
        pass

    @abc.abstractmethod
    async def execute(self, data: Any) -> Any:
        """
        Execute the main logic of the plugin.
        """
        pass

    @abc.abstractmethod
    async def cleanup(self) -> None:
        """
        Release resources and safely shutdown the plugin.
        """
        pass
