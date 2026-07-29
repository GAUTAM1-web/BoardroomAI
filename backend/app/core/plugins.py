from __future__ import annotations

import importlib
import os
from dataclasses import dataclass
from typing import Any, Protocol


class BoardroomPlugin(Protocol):
    name: str
    plugin_type: str

    def capabilities(self) -> dict[str, Any]:
        ...


@dataclass(frozen=True)
class RegisteredPlugin:
    name: str
    plugin_type: str
    module: str
    capabilities: dict[str, Any]


PLUGIN_TYPES = {
    "provider",
    "analytics",
    "exporter",
    "executive_module",
    "workflow_extension",
}


def discover_plugins(extra_modules: str | None = None) -> list[RegisteredPlugin]:
    modules = _configured_modules(extra_modules)
    plugins: list[RegisteredPlugin] = []
    for module_name in modules:
        try:
            module = importlib.import_module(module_name)
        except Exception:
            continue
        register = getattr(module, "register", None)
        if not callable(register):
            continue
        plugin = register()
        plugin_type = str(getattr(plugin, "plugin_type", "workflow_extension"))
        if plugin_type not in PLUGIN_TYPES:
            plugin_type = "workflow_extension"
        capabilities = plugin.capabilities() if hasattr(plugin, "capabilities") else {}
        plugins.append(
            RegisteredPlugin(
                name=str(getattr(plugin, "name", module_name)),
                plugin_type=plugin_type,
                module=module_name,
                capabilities=capabilities if isinstance(capabilities, dict) else {},
            )
        )
    return plugins


def plugin_manifest(extra_modules: str | None = None) -> dict[str, Any]:
    plugins = discover_plugins(extra_modules)
    by_type = {plugin_type: 0 for plugin_type in sorted(PLUGIN_TYPES)}
    for plugin in plugins:
        by_type[plugin.plugin_type] = by_type.get(plugin.plugin_type, 0) + 1
    return {
        "plugin_types": sorted(PLUGIN_TYPES),
        "registered_count": len(plugins),
        "by_type": by_type,
        "plugins": [
            {
                "name": plugin.name,
                "type": plugin.plugin_type,
                "module": plugin.module,
                "capabilities": plugin.capabilities,
            }
            for plugin in plugins
        ],
        "auto_discovery": {
            "environment_variable": "BOARDROOMAI_PLUGIN_MODULES",
            "format": "comma-separated Python module paths exposing register()",
        },
    }


def _configured_modules(extra_modules: str | None) -> list[str]:
    raw = (
        extra_modules
        if extra_modules is not None
        else os.getenv("BOARDROOMAI_PLUGIN_MODULES", "")
    )
    return [module.strip() for module in raw.split(",") if module.strip()]
