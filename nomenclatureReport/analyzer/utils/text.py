from __future__ import annotations

import re


def strip_suffix(value: str, suffix: str) -> str:
    if value.endswith(suffix):
        return value[: -len(suffix)]
    return value


def is_title_case_name(value: str) -> bool:
    if not value:
        return False
    tokens = value.split("_")
    return all(is_title_case_token(token) for token in tokens)


def is_title_case_token(token: str) -> bool:
    if not token:
        return False
    return bool(re.fullmatch(r"[A-Z][a-z0-9]*", token))


def has_internal_camel_case(token: str) -> bool:
    return bool(re.search(r"[a-z][A-Z]", token))


def is_title_case_label(label: str) -> bool:
    if not label:
        return False
    parts = re.split(r"[ -]", label)
    return all(is_title_case_label_token(part) for part in parts if part)


def is_title_case_label_token(token: str) -> bool:
    if token.isupper():
        return True
    if not token[0].isupper():
        return False
    if len(token) == 1:
        return True
    return token[1:].islower()
