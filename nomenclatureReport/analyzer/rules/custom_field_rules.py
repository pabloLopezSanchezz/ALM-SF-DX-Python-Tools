from __future__ import annotations

from nomenclatureReport.analyzer.engine.rule_engine import RuleContext
from nomenclatureReport.analyzer.models.component import Component, FieldMetadata
from nomenclatureReport.analyzer.models.issue import Issue
from nomenclatureReport.analyzer.models.rule import Rule
from nomenclatureReport.analyzer.utils.text import (
    has_internal_camel_case,
    is_title_case_label,
    is_title_case_name,
    strip_suffix,
)


def rule_custom_field_name_format(
    component: Component,
    context: RuleContext,
    rule: Rule,
) -> list[Issue]:
    metadata = require_field_metadata(component)
    if not metadata:
        return []

    if not metadata.api_name.endswith("__c"):
        return [
            build_issue(
                component,
                rule,
                "Custom field API name must end with __c.",
            )
        ]

    base_name = strip_suffix(metadata.api_name, "__c")
    if not is_title_case_name(base_name):
        return [
            build_issue(
                component,
                rule,
                "Custom field API name must be Title Case tokens separated by underscores.",
            )
        ]

    return []


def rule_custom_field_technical_prefix(
    component: Component,
    context: RuleContext,
    rule: Rule,
) -> list[Issue]:
    metadata = require_field_metadata(component)
    if not metadata:
        return []

    prefixes = (
        "txt_",
        "str_",
        "num_",
        "int_",
        "dec_",
        "dt_",
        "dtm_",
        "cb_",
        "bln_",
        "pl_",
        "fx_",
    )

    base_name = strip_suffix(metadata.api_name, "__c").lower()
    if any(base_name.startswith(prefix) for prefix in prefixes):
        return [
            build_issue(
                component,
                rule,
                "Custom field API name must not start with technical prefixes.",
            )
        ]
    return []


def rule_custom_field_description(
    component: Component,
    context: RuleContext,
    rule: Rule,
) -> list[Issue]:
    metadata = require_field_metadata(component)
    if not metadata:
        return []

    if not metadata.description.strip():
        return [
            build_issue(
                component,
                rule,
                "Field description is mandatory.",
            )
        ]
    return []


def rule_custom_field_help_text(
    component: Component,
    context: RuleContext,
    rule: Rule,
) -> list[Issue]:
    metadata = require_field_metadata(component)
    if not metadata:
        return []

    if not metadata.inline_help_text.strip():
        return [
            build_issue(
                component,
                rule,
                "Field inline help text is mandatory.",
            )
        ]
    return []


def rule_custom_field_internal_camelcase(
    component: Component,
    context: RuleContext,
    rule: Rule,
) -> list[Issue]:
    metadata = require_field_metadata(component)
    if not metadata:
        return []

    base_name = strip_suffix(metadata.api_name, "__c")
    tokens = base_name.split("_")
    if any(has_internal_camel_case(token) for token in tokens):
        return [
            build_issue(
                component,
                rule,
                "Token contains internal CamelCase; consider separating with underscores.",
            )
        ]
    return []


def rule_boolean_prefix(
    component: Component,
    context: RuleContext,
    rule: Rule,
) -> list[Issue]:
    metadata = require_field_metadata(component)
    if not metadata:
        return []

    base_name = strip_suffix(metadata.api_name, "__c")
    if not (base_name.startswith("Is_") or base_name.startswith("Has_")):
        return [
            build_issue(
                component,
                rule,
                "Checkbox field API name must start with Is_ or Has_.",
            )
        ]
    return []


def rule_date_suffix(
    component: Component,
    context: RuleContext,
    rule: Rule,
) -> list[Issue]:
    return require_suffix(component, rule, "_Date__c", "Date")


def rule_datetime_suffix(
    component: Component,
    context: RuleContext,
    rule: Rule,
) -> list[Issue]:
    return require_suffix(component, rule, "_At__c", "DateTime")


def rule_time_suffix(
    component: Component,
    context: RuleContext,
    rule: Rule,
) -> list[Issue]:
    return require_suffix(component, rule, "_Time__c", "Time")


def rule_currency_suffix(
    component: Component,
    context: RuleContext,
    rule: Rule,
) -> list[Issue]:
    return prefer_suffix(component, rule, "_Amount__c", "Currency")


def rule_percent_suffix(
    component: Component,
    context: RuleContext,
    rule: Rule,
) -> list[Issue]:
    return prefer_suffix(component, rule, "_Pct__c", "Percent")


def rule_number_count_suffix(
    component: Component,
    context: RuleContext,
    rule: Rule,
) -> list[Issue]:
    metadata = require_field_metadata(component)
    if not metadata:
        return []

    if not metadata.api_name.endswith("_Count__c"):
        return [
            build_issue(
                component,
                rule,
                "If this field represents a count, use the _Count__c suffix.",
            )
        ]
    return []


def rule_external_id_naming(
    component: Component,
    context: RuleContext,
    rule: Rule,
) -> list[Issue]:
    metadata = require_field_metadata(component)
    if not metadata or not metadata.external_id:
        return []

    if not metadata.api_name.endswith("_Ext_Id__c"):
        return [
            build_issue(
                component,
                rule,
                "External ID fields must end with _Ext_Id__c.",
            )
        ]
    return []


def rule_external_id_unique(
    component: Component,
    context: RuleContext,
    rule: Rule,
) -> list[Issue]:
    metadata = require_field_metadata(component)
    if not metadata or not metadata.external_id:
        return []

    if not metadata.unique:
        return [
            build_issue(
                component,
                rule,
                "External ID fields are recommended to be unique.",
            )
        ]
    return []


def rule_lookup_role_based(
    component: Component,
    context: RuleContext,
    rule: Rule,
) -> list[Issue]:
    metadata = require_field_metadata(component)
    if not metadata:
        return []

    return [
        build_issue(
            component,
            rule,
            "Review lookup naming to ensure role-based semantics.",
        )
    ]


def rule_picklist_value_source(
    component: Component,
    context: RuleContext,
    rule: Rule,
) -> list[Issue]:
    metadata = require_field_metadata(component)
    if not metadata:
        return []

    if metadata.value_set_definition_labels:
        return []
    if metadata.value_set_name:
        return []

    api_name = strip_suffix(metadata.api_name, "__c")
    if (
        api_name in context.standard_value_sets
        or metadata.api_name in context.standard_value_sets
    ):
        return []

    return [
        build_issue(
            component,
            rule,
            "Picklist value source is not resolvable (inline, GVS, or standard).",
        )
    ]


def rule_picklist_labels_title_case(
    component: Component,
    context: RuleContext,
    rule: Rule,
) -> list[Issue]:
    metadata = require_field_metadata(component)
    if not metadata or not metadata.value_set_definition_labels:
        return []

    invalid_labels = [
        label
        for label in metadata.value_set_definition_labels
        if not is_title_case_label(label)
    ]
    if invalid_labels:
        return [
            build_issue(
                component,
                rule,
                f"Invalid picklist labels (not Title Case): {', '.join(invalid_labels)}.",
            )
        ]
    return []


def rule_picklist_prefer_gvs(
    component: Component,
    context: RuleContext,
    rule: Rule,
) -> list[Issue]:
    metadata = require_field_metadata(component)
    if not metadata or not metadata.value_set_definition_labels:
        return []

    label_key = tuple(metadata.value_set_definition_labels)
    matches = context.inline_picklist_map.get(label_key, [])
    if len(matches) <= 1:
        return []

    return [
        build_issue(
            component,
            rule,
            "Inline picklist values are reused in multiple fields; "
            "consider a Global Value Set.",
        )
    ]


def rule_formula_type_detection(
    component: Component,
    context: RuleContext,
    rule: Rule,
) -> list[Issue]:
    metadata = require_field_metadata(component)
    if not metadata or not metadata.formula:
        return []

    if metadata.field_type != "Formula":
        return [
            build_issue(
                component,
                rule,
                f"Field contains formula but type is '{metadata.field_type}'.",
            )
        ]
    return []


def rule_formula_derivation_documented(
    component: Component,
    context: RuleContext,
    rule: Rule,
) -> list[Issue]:
    metadata = require_field_metadata(component)
    if not metadata or not metadata.formula:
        return []

    if not metadata.description.strip():
        return [
            build_issue(
                component,
                rule,
                "Formula fields should document derivation in the description.",
            )
        ]

    return [
        build_issue(
            component,
            rule,
            "Review formula description to ensure derivation is documented.",
        )
    ]


def require_field_metadata(component: Component) -> FieldMetadata | None:
    if not isinstance(component.metadata, FieldMetadata):
        return None
    return component.metadata


def require_suffix(
    component: Component,
    rule: Rule,
    suffix: str,
    field_type: str,
) -> list[Issue]:
    metadata = require_field_metadata(component)
    if not metadata:
        return []

    if not metadata.api_name.endswith(suffix):
        return [
            build_issue(
                component,
                rule,
                f"{field_type} fields must end with {suffix}.",
            )
        ]
    return []


def prefer_suffix(
    component: Component,
    rule: Rule,
    suffix: str,
    field_type: str,
) -> list[Issue]:
    metadata = require_field_metadata(component)
    if not metadata:
        return []

    if not metadata.api_name.endswith(suffix):
        return [
            build_issue(
                component,
                rule,
                f"{field_type} fields are expected to end with {suffix}.",
            )
        ]
    return []


def build_issue(component: Component, rule: Rule, message: str) -> Issue:
    return Issue(
        rule_id=rule.rule_id,
        severity=rule.severity,
        message=message,
        component_name=component.name,
        component_path=component.path,
        component_type=rule.component_type,
        pending_review=rule.pending_review,
    )
