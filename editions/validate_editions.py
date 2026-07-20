#!/usr/bin/env python3
"""Validate technical-edition configs without credentials or network access.

The repository deliberately uses only the Python standard library here.  The
small schema evaluator implements the JSON Schema keywords used by
``edition.schema.json``; the semantic pass then resolves every editorial
section explicitly and never supplies a current-affairs fallback.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = REPO_ROOT / "editions/_schema/edition.schema.json"
DEFAULT_CONFIGS = (
    REPO_ROOT / "editions/ai/edition.json",
    REPO_ROOT / "editions/eda/edition.json",
)

EDITORIAL_REFERENCE_KEYS = (
    "charter",
    "roles",
    "sources",
    "evidence_rubric",
    "selection_rules",
    "article_template",
    "no_publish_template",
)
CURRENT_AFFAIRS_FALLBACKS = {
    "newsroom/charter.md",
    "newsroom/personas",
    "newsroom/sources.md",
}


class EditionValidationError(ValueError):
    """Raised when a technical-edition config is unsafe or incomplete."""


def load_json(path: Path) -> Any:
    try:
        with path.open(encoding="utf-8") as stream:
            return json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        raise EditionValidationError(f"cannot load {path}: {exc}") from exc


def _json_pointer(root: Mapping[str, Any], pointer: str) -> Mapping[str, Any]:
    if not pointer.startswith("#/"):
        raise EditionValidationError(f"unsupported schema reference: {pointer}")
    value: Any = root
    for raw_part in pointer[2:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        try:
            value = value[part]
        except (KeyError, TypeError) as exc:
            raise EditionValidationError(f"unresolved schema reference: {pointer}") from exc
    if not isinstance(value, Mapping):
        raise EditionValidationError(f"schema reference is not an object: {pointer}")
    return value


def _matches_type(instance: Any, expected: str) -> bool:
    return {
        "object": isinstance(instance, dict),
        "array": isinstance(instance, list),
        "string": isinstance(instance, str),
        "boolean": isinstance(instance, bool),
        "number": isinstance(instance, (int, float)) and not isinstance(instance, bool),
        "integer": isinstance(instance, int) and not isinstance(instance, bool),
        "null": instance is None,
    }.get(expected, False)


def _schema_errors(
    instance: Any,
    schema: Mapping[str, Any],
    root_schema: Mapping[str, Any],
    location: str,
) -> List[str]:
    errors: List[str] = []

    if "$ref" in schema:
        referenced = _json_pointer(root_schema, schema["$ref"])
        errors.extend(_schema_errors(instance, referenced, root_schema, location))

    for index, subschema in enumerate(schema.get("allOf", [])):
        errors.extend(
            _schema_errors(instance, subschema, root_schema, f"{location}.allOf[{index}]")
        )

    if "const" in schema and instance != schema["const"]:
        errors.append(f"{location}: must equal {schema['const']!r}")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{location}: must be one of {schema['enum']!r}")

    expected_type = schema.get("type")
    if expected_type is not None and not _matches_type(instance, expected_type):
        errors.append(f"{location}: expected {expected_type}")
        return errors

    if isinstance(instance, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in instance:
                errors.append(f"{location}: missing required property {key!r}")

        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in instance:
                if key not in properties:
                    errors.append(f"{location}: unexpected property {key!r}")
        for key, subschema in properties.items():
            if key in instance:
                errors.extend(
                    _schema_errors(instance[key], subschema, root_schema, f"{location}.{key}")
                )

    if isinstance(instance, list):
        if len(instance) < schema.get("minItems", 0):
            errors.append(f"{location}: too few items")
        if "maxItems" in schema and len(instance) > schema["maxItems"]:
            errors.append(f"{location}: too many items")
        if schema.get("uniqueItems"):
            fingerprints = [
                json.dumps(item, sort_keys=True, ensure_ascii=False) for item in instance
            ]
            if len(fingerprints) != len(set(fingerprints)):
                errors.append(f"{location}: items must be unique")
        if "items" in schema:
            for index, item in enumerate(instance):
                errors.extend(
                    _schema_errors(
                        item,
                        schema["items"],
                        root_schema,
                        f"{location}[{index}]",
                    )
                )
        if "contains" in schema:
            matching = sum(
                not _schema_errors(item, schema["contains"], root_schema, location)
                for item in instance
            )
            if matching < schema.get("minContains", 1):
                errors.append(f"{location}: does not contain the required value")

    if isinstance(instance, str):
        if len(instance) < schema.get("minLength", 0):
            errors.append(f"{location}: string is too short")
        if "pattern" in schema and re.search(schema["pattern"], instance) is None:
            errors.append(f"{location}: does not match {schema['pattern']!r}")

    return errors


def validate_schema(instance: Any, schema: Mapping[str, Any]) -> None:
    errors = _schema_errors(instance, schema, schema, "$")
    if errors:
        raise EditionValidationError("schema validation failed: " + "; ".join(errors))


def _editorial_references(config: Mapping[str, Any]) -> Iterable[Tuple[str, Mapping[str, str]]]:
    editorial = config["editorial"]
    for key in EDITORIAL_REFERENCE_KEYS:
        yield key, editorial[key]
    yield "release_gates.common", editorial["release_gates"]["common"]
    yield "release_gates.edition", editorial["release_gates"]["edition"]


def _resolve_section_reference(
    label: str,
    reference: Mapping[str, str],
    edition_id: str,
    repo_root: Path,
) -> str:
    raw_path = reference["path"]
    relative = PurePosixPath(raw_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise EditionValidationError(f"{label}: unsafe reference path {raw_path!r}")
    if relative.parts and relative.parts[0] == "newsroom":
        raise EditionValidationError(
            f"{label}: current-affairs fallback is forbidden: {raw_path}"
        )
    if len(relative.parts) >= 2 and relative.parts[0] == "editions":
        referenced_edition = relative.parts[1]
        if referenced_edition in {"ai", "eda"} and referenced_edition != edition_id:
            raise EditionValidationError(
                f"{label}: cross-edition fallback is forbidden: {raw_path}"
            )

    resolved = (repo_root / Path(*relative.parts)).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise EditionValidationError(f"{label}: path escapes repository: {raw_path}") from exc
    if not resolved.is_file():
        raise EditionValidationError(
            f"{label}: referenced file is missing; no fallback attempted: {raw_path}"
        )

    heading = reference["heading"]
    occurrences = resolved.read_text(encoding="utf-8").splitlines().count(heading)
    if occurrences != 1:
        raise EditionValidationError(
            f"{label}: heading must occur exactly once (found {occurrences}); "
            f"no fallback attempted: {raw_path} :: {heading}"
        )
    return f"{raw_path}#{heading}"


def validate_config(
    config: Mapping[str, Any],
    schema: Mapping[str, Any],
    repo_root: Path = REPO_ROOT,
) -> Dict[str, Any]:
    validate_schema(config, schema)
    edition_id = config["id"]

    forbidden = set(config["forbidden_fallbacks"])
    missing_forbidden = CURRENT_AFFAIRS_FALLBACKS - forbidden
    if missing_forbidden:
        raise EditionValidationError(
            "forbidden_fallbacks omits current-affairs paths: "
            + ", ".join(sorted(missing_forbidden))
        )
    peer = "eda" if edition_id == "ai" else "ai"
    if f"editions/{peer}" not in forbidden:
        raise EditionValidationError(
            f"forbidden_fallbacks must forbid peer edition editions/{peer}"
        )

    resolved_sections = [
        _resolve_section_reference(label, reference, edition_id, repo_root)
        for label, reference in _editorial_references(config)
    ]
    return {
        "id": edition_id,
        "profile_class": config["profile_class"],
        "resolved_section_references": len(resolved_sections),
        "publish_requires_human_approval": config["publication"][
            "publish_requires_human_approval"
        ],
        "fallback_policy": "explicit-failure",
    }


def validate_config_path(
    config_path: Path,
    schema: Mapping[str, Any],
    repo_root: Path = REPO_ROOT,
) -> Dict[str, Any]:
    config = load_json(config_path)
    result = validate_config(config, schema, repo_root)
    if config_path.parent.name != result["id"]:
        raise EditionValidationError(
            f"config directory {config_path.parent.name!r} does not match id {result['id']!r}"
        )
    result["config"] = config_path.relative_to(repo_root).as_posix()
    return result


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument(
        "--config",
        action="append",
        type=Path,
        dest="configs",
        help="config path; repeat for more than one (defaults to AI and EDA)",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] = ()) -> int:
    args = _parse_args(argv)
    configs = tuple(args.configs) if args.configs else DEFAULT_CONFIGS
    try:
        schema = load_json(args.schema)
        results = [validate_config_path(path.resolve(), schema) for path in configs]
        ids = [result["id"] for result in results]
        if not args.configs and sorted(ids) != ["ai", "eda"]:
            raise EditionValidationError("default validation must include AI and EDA exactly once")
    except EditionValidationError as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False))
        return 2

    print(
        json.dumps(
            {
                "status": "passed",
                "schema": args.schema.resolve().relative_to(REPO_ROOT).as_posix(),
                "editions": results,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
