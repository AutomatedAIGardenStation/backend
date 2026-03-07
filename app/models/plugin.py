from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

class PluginManifest(BaseModel):
    name: str = Field(..., description="Unique name of the plugin")
    version: str = Field(..., description="Version of the plugin")
    description: Optional[str] = Field(None, description="Description of the plugin")
    entrypoint: str = Field(..., description="Module path to the plugin class, e.g., 'my_plugin.plugin.MyPlugin'")
    scopes: List[str] = Field(default_factory=list, description="List of permission scopes requested by the plugin")
    config_schema: Optional[Dict[str, Any]] = Field(None, description="Optional JSON schema for plugin configuration")
