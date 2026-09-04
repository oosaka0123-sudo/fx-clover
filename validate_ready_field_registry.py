"""Validate that every v1.23 READY manual field has evidence metadata.

The validator uses AST instead of importing watch_monitor_v1_4.py so CI does not
need pandas/matplotlib and the hash-pinned runtime remains untouched.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RUNTIME_SOURCE = ROOT / "watch_monitor_v1_4.py"
REGISTRY_PATH = ROOT / "knowledge" / "ready_manual_field_registry.json"


def extract_string_list_assignment(source: str, name: str) -> list[str]:
    tree = ast.parse(source)
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            continue
        value = ast.literal_eval(node.value)
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise ValueError(f"{name} must be a list[str]")
        return value
    raise ValueError(f"assignment not found: {name}")


def validate(runtime_source: Path = RUNTIME_SOURCE, registry_path: Path = REGISTRY_PATH) -> dict:
    runtime_fields = extract_string_list_assignment(runtime_source.read_text(encoding="utf-8"), "MANUAL_COLUMNS")
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    fields = registry.get("fields", {})
    registry_fields = list(fields)

    errors: list[str] = []
    if registry.get("orders_enabled") is not False:
        errors.append("registry orders_enabled must be false")
    if set(runtime_fields) != set(registry_fields):
        missing = sorted(set(runtime_fields) - set(registry_fields))
        extra = sorted(set(registry_fields) - set(runtime_fields))
        if missing:
            errors.append(f"missing registry fields: {missing}")
        if extra:
            errors.append(f"extra registry fields: {extra}")

    for name in runtime_fields:
        item = fields.get(name)
        if not isinstance(item, dict):
            continue
        if not item.get("classification"):
            errors.append(f"{name}: classification required")
        if item.get("input_mode_v1_23") != "MANUAL_REQUIRED":
            errors.append(f"{name}: v1.23 input mode must remain MANUAL_REQUIRED")
        if item.get("production_auto_allowed") is not False:
            errors.append(f"{name}: production_auto_allowed must be false")
        if item.get("official_concept_supported") is not True:
            errors.append(f"{name}: official_concept_supported must be true")
        evidence = item.get("official_evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{name}: official_evidence must be a non-empty list")
        elif any(not isinstance(url, str) or not url.startswith("https://fx-clover.com/") for url in evidence):
            errors.append(f"{name}: official_evidence must contain only fx-clover.com URLs")
        unresolved = item.get("unresolved")
        if not isinstance(unresolved, list) or not unresolved:
            errors.append(f"{name}: unresolved list required; do not imply false precision")
        if not item.get("safe_interpretation"):
            errors.append(f"{name}: safe_interpretation required")

    return {
        "schema_version": "1.0",
        "status": "PASS" if not errors else "FAIL",
        "runtime_fields": runtime_fields,
        "registry_fields": registry_fields,
        "errors": errors,
        "orders_enabled": False,
    }


def main() -> int:
    result = validate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
