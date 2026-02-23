from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class FieldMetadata:
    api_name: str
    field_type: str
    description: str
    inline_help_text: str
    formula: str | None
    external_id: bool
    unique: bool
    value_set_definition_labels: list[str]
    value_set_name: str | None


@dataclass(frozen=True)
class ObjectMetadata:
    api_name: str
    description: str


@dataclass(frozen=True)
class Component:
    name: str
    path: Path
    component_types: set[str]
    metadata: FieldMetadata | ObjectMetadata | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "path": str(self.path),
            "component_types": sorted(self.component_types),
        }
