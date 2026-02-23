from __future__ import annotations

from nomenclatureReport.analyzer.engine.rule_engine import RuleContext
from nomenclatureReport.analyzer.models.component import Component, ObjectMetadata
from nomenclatureReport.analyzer.models.issue import Issue
from nomenclatureReport.analyzer.models.rule import Rule


def rule_object_description(
    component: Component,
    context: RuleContext,
    rule: Rule,
) -> list[Issue]:
    metadata = component.metadata
    if not isinstance(metadata, ObjectMetadata):
        return []

    if not metadata.description.strip():
        return [
            Issue(
                rule_id=rule.rule_id,
                severity=rule.severity,
                message="Custom object description is mandatory.",
                component_name=component.name,
                component_path=component.path,
                component_type=rule.component_type,
                pending_review=rule.pending_review,
            )
        ]
    return []
