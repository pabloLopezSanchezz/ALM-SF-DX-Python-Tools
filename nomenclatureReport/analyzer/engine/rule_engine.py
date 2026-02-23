from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from nomenclatureReport.analyzer.models.component import Component, FieldMetadata
from nomenclatureReport.analyzer.models.issue import Issue
from nomenclatureReport.analyzer.models.report import Report
from nomenclatureReport.analyzer.models.rule import Rule
from nomenclatureReport.analyzer.utils.fs import read_json


RuleFunction = Callable[[Component, "RuleContext", Rule], list[Issue]]


@dataclass(frozen=True)
class RuleContext:
    standard_value_sets: set[str]
    inline_picklist_map: dict[tuple[str, ...], list[str]]


class RuleEngine:
    def __init__(
        self,
        rules_path: Path,
        rule_registry: dict[str, RuleFunction],
        standard_value_sets: set[str],
    ) -> None:
        self._rules_path = rules_path
        self._rule_registry = rule_registry
        self._standard_value_sets = standard_value_sets
        self._rules = self._load_rules()

    def evaluate(self, components: list[Component]) -> Report:
        context = RuleContext(
            standard_value_sets=self._standard_value_sets,
            inline_picklist_map=build_inline_picklist_map(components),
        )

        issues: list[Issue] = []
        missing_rule_ids: set[str] = set()

        for component in components:
            for rule in self._rules:
                if rule.component_type not in component.component_types:
                    continue
                if not rule_applies_to_component(rule, component):
                    continue
                rule_func = self._rule_registry.get(rule.rule_id)
                if not rule_func:
                    missing_rule_ids.add(rule.rule_id)
                    continue
                issues.extend(rule_func(component, context, rule))

        return Report(issues=issues, missing_rule_ids=sorted(missing_rule_ids))

    def _load_rules(self) -> list[Rule]:
        raw_rules = read_json(self._rules_path)
        rules: list[Rule] = []
        for raw in raw_rules:
            rules.append(
                Rule(
                    rule_id=raw["ruleId"],
                    component_type=raw["component_type"],
                    rule=raw["rule"],
                    severity=raw["severity"],
                    pending_review=raw["pending_review"],
                    description=raw["description"],
                    example=raw.get("example", ""),
                    applies_when=raw.get("applies_when"),
                ),
            )
        return rules


def build_inline_picklist_map(
    components: list[Component],
) -> dict[tuple[str, ...], list[str]]:
    label_map: dict[tuple[str, ...], list[str]] = {}
    for component in components:
        metadata = component.metadata
        if not isinstance(metadata, FieldMetadata):
            continue
        if not metadata.value_set_definition_labels:
            continue
        label_key = tuple(metadata.value_set_definition_labels)
        label_map.setdefault(label_key, []).append(component.name)
    return label_map


def rule_applies_to_component(rule: Rule, component: Component) -> bool:
    if not rule.applies_when:
        return True

    metadata = component.metadata
    if not isinstance(metadata, FieldMetadata):
        return False

    conditions = rule.applies_when

    expected_field_type = conditions.get("field_type")
    if expected_field_type is not None and metadata.field_type != expected_field_type:
        return False

    expected_field_types = conditions.get("field_type_in")
    if expected_field_types is not None:
        if not isinstance(expected_field_types, list):
            return False
        if metadata.field_type not in expected_field_types:
            return False

    expected_external_id = conditions.get("external_id")
    if expected_external_id is not None and metadata.external_id != expected_external_id:
        return False

    expected_has_formula = conditions.get("has_formula")
    if expected_has_formula is not None:
        has_formula = bool(metadata.formula)
        if has_formula != expected_has_formula:
            return False

    return True
