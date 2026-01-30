#!/usr/bin/env python3
import re
import sys
from pathlib import Path


def normalize_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def extract_tests_block(description: str) -> str:
    pattern = re.compile(
        r"```[ \t]*testsToBeRun[ \t]*\n(.*?)\n```",
        re.IGNORECASE | re.DOTALL,
    )
    match = pattern.search(description)
    if not match:
        return ""
    return match.group(1)


def clean_line(line: str) -> str:
    line = line.strip()
    if not line:
        return ""
    if line.startswith(("-", "*")):
        line = line[1:].strip()
    line = re.split(r"[#]|//", line, maxsplit=1)[0].strip()
    return line


def split_tests(raw: str) -> list[str]:
    raw = normalize_text(raw)
    parts = []
    for line in raw.split("\n"):
        cleaned = clean_line(line)
        if not cleaned:
            continue
        if "," in cleaned:
            parts.extend([p.strip() for p in cleaned.split(",") if p.strip()])
        else:
            parts.append(cleaned)
    return parts


def normalize_tests(tests: list[str]) -> list[str]:
    seen = set()
    result = []
    for test in tests:
        test = test.strip()
        if not test:
            continue
        if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", test):
            # Keep non-standard names but strip surrounding quotes/spaces
            test = test.strip("\"' ")
        if test and test not in seen:
            seen.add(test)
            result.append(test)
    return result


def main() -> int:
    if len(sys.argv) < 2:
        print("", end="")
        return 0
    path = Path(sys.argv[1])
    if not path.exists():
        print("", end="")
        return 0
    try:
        description = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        print("", end="")
        return 0

    description = normalize_text(description)
    block = extract_tests_block(description)
    if not block:
        print("", end="")
        return 0

    tests = split_tests(block)
    tests = normalize_tests(tests)
    print(",".join(tests), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
