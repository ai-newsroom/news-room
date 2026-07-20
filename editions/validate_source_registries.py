#!/usr/bin/env python3
"""Validate AI/EDA source registries without network access or fallback."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence, Set
from urllib.parse import urlparse

if __package__:
    from editions.validate_editions import (
        REPO_ROOT,
        EditionValidationError,
        load_json,
        validate_schema,
    )
else:
    from validate_editions import (
        REPO_ROOT,
        EditionValidationError,
        load_json,
        validate_schema,
    )


DEFAULT_SCHEMA = REPO_ROOT / "editions/_schema/source-registry.schema.json"
DEFAULT_REGISTRIES = (
    REPO_ROOT / "editions/ai/sources/primary-sources.json",
    REPO_ROOT / "editions/eda/sources/primary-sources.json",
)
REQUIRED_SOURCE_TYPES = {
    "ai": {
        "model-system-card",
        "paper-index",
        "code-repository",
        "release-notes",
        "independent-evaluation",
    },
    "eda": {
        "tool-release",
        "standard",
        "paper-index",
        "public-benchmark",
        "open-source-flow",
    },
}


def validate_registry(
    registry: Mapping[str, Any],
    schema: Mapping[str, Any],
    expected_edition: str | None = None,
) -> Dict[str, Any]:
    validate_schema(registry, schema)
    edition = registry["edition"]
    if expected_edition is not None and edition != expected_edition:
        raise EditionValidationError(
            f"registry edition {edition!r} does not match path edition {expected_edition!r}"
        )

    if registry["forbidden_imports"] != ["newsroom/sources.md"]:
        raise EditionValidationError("current-affairs source fallback must remain forbidden")

    ids = [source["id"] for source in registry["sources"]]
    duplicate_ids = sorted({source_id for source_id in ids if ids.count(source_id) > 1})
    if duplicate_ids:
        raise EditionValidationError("duplicate source ids: " + ", ".join(duplicate_ids))

    observed_types: Set[str] = set()
    primary_count = 0
    secondary_count = 0
    limited_access_count = 0
    for source in registry["sources"]:
        observed_types.add(source["source_type"])
        parsed = urlparse(source["canonical_url"])
        if parsed.scheme != "https" or not parsed.netloc:
            raise EditionValidationError(
                f"{source['id']}: canonical_url must be an absolute HTTPS URL"
            )
        if source["default_relation"] == "primary":
            primary_count += 1
        else:
            secondary_count += 1
            if not set(source["evidence_codes"]) & {"I1", "S1"}:
                raise EditionValidationError(
                    f"{source['id']}: secondary source needs I1 or S1 evidence semantics"
                )
        if source["access"]["status"] != "public":
            limited_access_count += 1

    missing_types = REQUIRED_SOURCE_TYPES[edition] - observed_types
    if missing_types:
        raise EditionValidationError(
            f"{edition}: missing required source types: " + ", ".join(sorted(missing_types))
        )

    return {
        "edition": edition,
        "registry_id": registry["registry_id"],
        "source_count": len(registry["sources"]),
        "source_types": sorted(observed_types),
        "primary_count": primary_count,
        "secondary_count": secondary_count,
        "limited_access_count": limited_access_count,
        "current_affairs_imported": False,
    }


def validate_registry_path(
    path: Path,
    schema: Mapping[str, Any],
) -> Dict[str, Any]:
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(REPO_ROOT)
    except ValueError as exc:
        raise EditionValidationError(f"registry path escapes repository: {path}") from exc
    if len(relative.parts) < 4 or relative.parts[:1] != ("editions",):
        raise EditionValidationError(f"registry path is outside an edition: {relative}")
    expected_edition = relative.parts[1]
    result = validate_registry(load_json(resolved), schema, expected_edition)
    result["path"] = relative.as_posix()
    return result


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--registry", action="append", type=Path, dest="registries")
    return parser.parse_args(argv)


def main(argv: Sequence[str] = ()) -> int:
    args = _parse_args(argv)
    registries = tuple(args.registries) if args.registries else DEFAULT_REGISTRIES
    try:
        schema = load_json(args.schema)
        results = [validate_registry_path(path, schema) for path in registries]
        if not args.registries and sorted(item["edition"] for item in results) != ["ai", "eda"]:
            raise EditionValidationError("default validation must include AI and EDA exactly once")
    except EditionValidationError as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False))
        return 2

    print(
        json.dumps(
            {"status": "passed", "registries": results},
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
