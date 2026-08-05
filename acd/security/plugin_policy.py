"""Strict validation for in-process plugin manifests."""

from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Any

from acd.security.security_errors import PluginRejectedError

MAX_PLUGIN_MANIFEST_BYTES = 64 * 1024
_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")
_VERSION = re.compile(r"^[0-9]+(?:\.[0-9]+){0,3}(?:[-+][A-Za-z0-9.-]+)?$")


def validate_plugin_name(value: object) -> str:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise PluginRejectedError("Plugin name is invalid")
    return value


def validate_plugin_manifest(
    manifest: object, *, expected_name: str
) -> tuple[dict[str, Any], str, str]:
    if not isinstance(manifest, Mapping):
        raise PluginRejectedError("Plugin manifest root is invalid")
    name = validate_plugin_name(manifest.get("name"))
    if name != expected_name:
        raise PluginRejectedError("Plugin manifest name does not match")
    version = manifest.get("version")
    minimum = manifest.get("min_app_version")
    if not isinstance(version, str) or not _VERSION.fullmatch(version):
        raise PluginRejectedError("Plugin version is invalid")
    if not isinstance(minimum, str) or not _VERSION.fullmatch(minimum):
        raise PluginRejectedError("Plugin minimum version is invalid")
    entry_point = manifest.get("entry_point")
    if not isinstance(entry_point, str) or entry_point.count(":") != 1:
        raise PluginRejectedError("Plugin entry point is invalid")
    module_name, class_name = entry_point.split(":")
    if not _IDENTIFIER.fullmatch(module_name) or not _IDENTIFIER.fullmatch(class_name):
        raise PluginRejectedError("Plugin entry point is invalid")
    return dict(manifest), module_name, class_name

