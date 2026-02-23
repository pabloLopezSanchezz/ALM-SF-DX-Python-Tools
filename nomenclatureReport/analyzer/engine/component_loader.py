from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from nomenclatureReport.analyzer.models.component import (
    Component,
    FieldMetadata,
    ObjectMetadata,
)
from nomenclatureReport.analyzer.utils.fs import iter_files
from nomenclatureReport.analyzer.utils.text import strip_suffix
from nomenclatureReport.analyzer.utils.xml import get_child_text, parse_xml

NAMESPACE_FILTER_COMPONENT_TYPES: set[str] = {"CustomObject", "CustomField"}


@dataclass(frozen=True)
class ComponentLoadResult:
    components: list[Component]
    standard_value_sets: set[str]


def load_components(
    project_path: Path,
    namespace_filter_component_types: set[str] | None = None,
) -> tuple[list[Component], set[str]]:
    if namespace_filter_component_types is None:
        namespace_filter_component_types = set(NAMESPACE_FILTER_COMPONENT_TYPES)

    standard_value_sets = load_standard_value_sets(project_path)
    components: list[Component] = []

    for object_file in iter_object_files(project_path):
        component = parse_custom_object(
            object_file,
            apply_custom_filter="CustomObject" in namespace_filter_component_types,
        )
        if component:
            components.append(component)

    for field_file in iter_field_files(project_path):
        component = parse_custom_field(
            field_file,
            apply_custom_filter="CustomField" in namespace_filter_component_types,
        )
        if component:
            components.append(component)

    return components, standard_value_sets


def iter_object_files(project_path: Path) -> Iterable[Path]:
    for file_path in iter_files(project_path, suffix=".object-meta.xml"):
        if "objects" in file_path.parts and "fields" not in file_path.parts:
            yield file_path


def iter_field_files(project_path: Path) -> Iterable[Path]:
    for file_path in iter_files(project_path, suffix=".field-meta.xml"):
        if "objects" in file_path.parts and "fields" in file_path.parts:
            yield file_path


def load_standard_value_sets(project_path: Path) -> set[str]:
    names: set[str] = set()
    for file_path in iter_files(
        project_path,
        suffix=".standardValueSet-meta.xml",
    ):
        if "standardValueSets" not in file_path.parts:
            continue
        name = strip_suffix(file_path.name, ".standardValueSet-meta.xml")
        if name:
            names.add(name)
    return names


def parse_custom_object(file_path: Path, apply_custom_filter: bool = True) -> Component | None:
    root = parse_xml(file_path)
    if root is None:
        return None

    api_name = strip_suffix(file_path.name, ".object-meta.xml")
    if apply_custom_filter and not should_analyze_custom_component(api_name):
        return None

    description = get_child_text(root, "description")

    metadata = ObjectMetadata(
        api_name=api_name,
        description=description,
    )

    return Component(
        name=api_name,
        path=file_path,
        component_types={"CustomObject"},
        metadata=metadata,
    )


def parse_custom_field(file_path: Path, apply_custom_filter: bool = True) -> Component | None:
    root = parse_xml(file_path)
    if root is None:
        return None

    api_name = strip_suffix(file_path.name, ".field-meta.xml")
    if apply_custom_filter and not should_analyze_custom_component(api_name):
        return None

    field_type = get_child_text(root, "type")
    description = get_child_text(root, "description")
    inline_help = get_child_text(root, "inlineHelpText")
    formula = get_child_text(root, "formula")

    external_id = get_child_text(root, "externalId").lower() == "true"
    unique = get_child_text(root, "unique").lower() == "true"

    value_set_definition_labels = extract_value_set_labels(root)
    value_set_name = extract_value_set_name(root)

    metadata = FieldMetadata(
        api_name=api_name,
        field_type=field_type,
        description=description,
        inline_help_text=inline_help,
        formula=formula if formula else None,
        external_id=external_id,
        unique=unique,
        value_set_definition_labels=value_set_definition_labels,
        value_set_name=value_set_name,
    )

    component_types = build_field_component_types(metadata)

    return Component(
        name=api_name,
        path=file_path,
        component_types=component_types,
        metadata=metadata,
    )


def extract_value_set_labels(root) -> list[str]:
    labels: list[str] = []
    value_set = root.find("valueSet")
    if value_set is None:
        return labels

    definition = value_set.find("valueSetDefinition")
    if definition is None:
        return labels

    for value in definition.findall("value"):
        label = get_child_text(value, "label")
        if label:
            labels.append(label)
    return labels


def extract_value_set_name(root) -> str | None:
    value_set = root.find("valueSet")
    if value_set is None:
        return None

    value_set_name = get_child_text(value_set, "valueSetName")
    return value_set_name if value_set_name else None


def build_field_component_types(metadata: FieldMetadata) -> set[str]:
    component_types = {"CustomField"}
    field_type = metadata.field_type

    if field_type == "Checkbox":
        component_types.add("CheckboxField")
    if field_type == "Date":
        component_types.add("DateField")
    if field_type == "DateTime":
        component_types.add("DateTimeField")
    if field_type == "Time":
        component_types.add("TimeField")
    if field_type == "Currency":
        component_types.add("CurrencyField")
    if field_type == "Percent":
        component_types.add("PercentField")
    if field_type == "Number":
        component_types.add("NumberField")
    if field_type in {"Lookup", "MasterDetail"}:
        component_types.add("LookupField")
    if field_type in {"Picklist", "MultiselectPicklist"}:
        component_types.add("PicklistField")
    if metadata.formula or field_type == "Formula":
        component_types.add("FormulaField")
    if metadata.external_id:
        component_types.add("ExternalIdField")

    return component_types


def should_analyze_custom_component(api_name: str) -> bool:
    """Analyze only custom non-managed components.

    Rules requested:
    - Custom component: ends with "__c"
    - Managed package component: starts with "namespace__"
      (must be excluded even if it also ends with "__c")
    """
    if not is_custom_component_name(api_name):
        return False
    if is_managed_package_component_name(api_name):
        return False
    return True


def is_custom_component_name(api_name: str) -> bool:
    return api_name.endswith("__c")


def is_managed_package_component_name(api_name: str) -> bool:
    if "__" not in api_name:
        return False

    # Local custom names like "Account_Email__c" or "Account__c" must not be
    # treated as managed package names.
    if api_name.endswith("__c") and api_name.count("__") == 1:
        return False

    namespace, separator, _ = api_name.partition("__")
    return bool(separator) and namespace.isalnum()
