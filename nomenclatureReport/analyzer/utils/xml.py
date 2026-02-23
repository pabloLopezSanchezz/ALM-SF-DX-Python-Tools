from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path


def parse_xml(file_path: Path) -> ET.Element | None:
    try:
        tree = ET.parse(file_path)
    except ET.ParseError:
        return None

    root = tree.getroot()
    strip_namespaces(root)
    return root


def strip_namespaces(element: ET.Element) -> None:
    for elem in element.iter():
        if "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]


def get_child_text(element: ET.Element, tag: str) -> str:
    child = element.find(tag)
    if child is None or child.text is None:
        return ""
    return child.text.strip()
