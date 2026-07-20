#!/usr/bin/env python3
"""Read-only stage-1 resolver for current-affairs, AI, and EDA editions."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Mapping, Optional, Sequence


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from editions.validate_editions import (  # noqa: E402
    EditionValidationError,
    load_json,
    validate_schema,
)


RUNTIME_SCHEMA = REPO_ROOT / "editions/_schema/runtime-edition.schema.json"
CONFIG_PATHS = {
    edition: REPO_ROOT / f"editions/{edition}/runtime.json"
    for edition in ("current-affairs", "ai", "eda")
}
INPUT_PATH_KEYS = {
    "workspace": "directory",
    "editorial_profile": "file",
    "sources": "file",
}
CURRENT_INPUT_PATH_KEYS = {
    "prompt": "file",
    "workflow": "file",
    "legacy_entrypoint": "file",
}
WRITE_ROOT_KEYS = {"content_root", "run_root", "decision_root"}
TECHNICAL_FALLBACKS = {
    "newsroom/charter.md",
    "newsroom/personas",
    "newsroom/sources.md",
}
EXPECTED_CURRENT_PATHS = {
    "workspace": "newsroom",
    "prompt": "prompts/daily-newsroom-single-claude.md",
    "workflow": "workflows/daily-newsroom-single-claude.json",
    "legacy_entrypoint": "scripts/publish-daily.sh",
    "editorial_profile": "newsroom/charter.md",
    "sources": "newsroom/sources.md",
    "content_root": "content",
    "run_root": "newsroom/artifacts",
    "decision_root": "newsroom/artifacts",
}


class ResolutionError(ValueError):
    """Raised when an edition cannot be resolved without unsafe fallback."""


def load_runtime_configs(
    config_paths: Mapping[str, Path] = CONFIG_PATHS,
) -> Dict[str, Mapping[str, Any]]:
    configs: Dict[str, Mapping[str, Any]] = {}
    for declared_id, path in config_paths.items():
        try:
            config = load_json(path)
        except EditionValidationError as error:
            raise ResolutionError(str(error)) from error
        configs[declared_id] = config
    return configs


def validate_and_resolve_all(
    configs: Mapping[str, Mapping[str, Any]],
    schema: Mapping[str, Any],
    repo_root: Path = REPO_ROOT,
) -> Dict[str, Mapping[str, Any]]:
    """Validate all three configs together so route/id collisions fail."""

    if set(configs) != {"current-affairs", "ai", "eda"}:
        raise ResolutionError(
            "runtime config set must contain current-affairs, ai, and eda exactly"
        )

    ids = []
    route_owners: Dict[str, str] = {}
    resolved: Dict[str, Mapping[str, Any]] = {}
    for declared_id in ("current-affairs", "ai", "eda"):
        config = configs[declared_id]
        try:
            validate_schema(config, schema)
        except EditionValidationError as error:
            raise ResolutionError(str(error)) from error

        edition_id = config["id"]
        if edition_id != declared_id:
            raise ResolutionError(
                f"config key {declared_id!r} does not match id {edition_id!r}"
            )
        ids.append(edition_id)
        route = config["site"]["route_prefix"]
        if route in route_owners:
            raise ResolutionError(
                f"duplicate route prefix {route!r}: "
                f"{route_owners[route]} and {edition_id}"
            )
        route_owners[route] = edition_id
        resolved[edition_id] = _resolve_config(config, repo_root)

    if len(ids) != len(set(ids)):
        raise ResolutionError("duplicate edition id")
    technical_roots = [
        resolved[edition]["normalized_paths"][key]["relative"]
        for edition in ("ai", "eda")
        for key in ("content_root", "run_root", "decision_root")
    ]
    if len(technical_roots) != len(set(technical_roots)):
        raise ResolutionError("technical write roots must be edition-isolated")
    return resolved


def _resolve_config(
    config: Mapping[str, Any], repo_root: Path
) -> Mapping[str, Any]:
    edition_id = config["id"]
    profile_class = config["profile_class"]
    if edition_id == "current-affairs":
        if profile_class != "current-affairs":
            raise ResolutionError(
                "current-affairs must use the current-affairs profile"
            )
        _validate_current_affairs(config)
    else:
        if profile_class != "technical":
            raise ResolutionError(
                f"{edition_id} must use the technical profile"
            )
        _validate_technical(config)

    normalized_paths = {}
    input_kinds = dict(INPUT_PATH_KEYS)
    if edition_id == "current-affairs":
        input_kinds.update(CURRENT_INPUT_PATH_KEYS)
    for key, raw_path in config["paths"].items():
        expected_kind = input_kinds.get(key)
        access = "read-only-input" if expected_kind else "declared-write-root"
        normalized_paths[key] = _normalize_repository_path(
            key,
            raw_path,
            repo_root,
            expected_kind=expected_kind,
            access=access,
        )

    relative_roots = [
        normalized_paths[key]["relative"] for key in WRITE_ROOT_KEYS
    ]
    if len(relative_roots) != len(set(relative_roots)):
        allowed_legacy_overlap = (
            edition_id == "current-affairs"
            and config["paths"]["run_root"]
            == config["paths"]["decision_root"]
        )
        if not allowed_legacy_overlap:
            raise ResolutionError(
                f"{edition_id}: content, run, and decision roots must be distinct"
            )

    return {
        "id": edition_id,
        "profile_class": profile_class,
        "normalized_paths": normalized_paths,
        "schedule": dict(config["schedule"]),
        "release": dict(config["release"]),
        "site": dict(config["site"]),
        "fallback_policy": (
            "legacy-explicit-paths"
            if edition_id == "current-affairs"
            else "technical-explicit-failure"
        ),
        "phase_plan": _phase_plan(edition_id, config),
    }


def _validate_current_affairs(config: Mapping[str, Any]) -> None:
    if config["paths"] != EXPECTED_CURRENT_PATHS:
        raise ResolutionError(
            "current-affairs paths must preserve the current "
            "newsroom, prompt, workflow, wrapper, and content roots"
        )
    schedule = config["schedule"]
    if not (
        schedule["enabled"] is True
        and schedule["managed_by"] == "external-cron"
    ):
        raise ResolutionError(
            "current-affairs must describe the existing external cron"
        )
    release = config["release"]
    if release != {
        "mode": "legacy-wrapper",
        "requires_human_approval": False,
        "git_write": True,
        "deploy": False,
    }:
        raise ResolutionError(
            "current-affairs release must describe, not change, the legacy wrapper"
        )
    if config["site"] != {
        "route_prefix": "/news",
        "include_in_legacy_home": True,
    }:
        raise ResolutionError(
            "current-affairs must preserve /news and the legacy home feed"
        )
    if config["forbidden_fallbacks"]:
        raise ResolutionError(
            "current-affairs uses explicit legacy paths, not a fallback list"
        )


def _validate_technical(config: Mapping[str, Any]) -> None:
    edition_id = config["id"]
    paths = config["paths"]
    unexpected_execution_paths = {"prompt", "workflow", "legacy_entrypoint"} & set(
        paths
    )
    if unexpected_execution_paths:
        raise ResolutionError(
            f"{edition_id}: stage 1 technical config must not declare executable "
            + ", ".join(sorted(unexpected_execution_paths))
        )
    expected_inputs = {
        "workspace": f"editions/{edition_id}",
        "editorial_profile": f"editions/{edition_id}/edition.json",
        "sources": f"editions/{edition_id}/sources/primary-sources.json",
        "content_root": f"content/{edition_id}",
        "run_root": f"var/runs/{edition_id}",
        "decision_root": f"decisions/{edition_id}",
    }
    if paths != expected_inputs:
        raise ResolutionError(
            f"{edition_id}: technical paths must be edition-owned and explicit"
        )

    schedule = config["schedule"]
    if not (
        schedule["enabled"] is False
        and schedule["managed_by"] == "none"
        and schedule["cadence"] == "on-demand"
    ):
        raise ResolutionError(
            f"{edition_id}: technical schedule must remain disabled"
        )
    release = config["release"]
    if release != {
        "mode": "prepare-only",
        "requires_human_approval": True,
        "git_write": False,
        "deploy": False,
    }:
        raise ResolutionError(
            f"{edition_id}: release must be prepare-only with human approval"
        )
    if config["site"] != {
        "route_prefix": f"/{edition_id}",
        "include_in_legacy_home": False,
    }:
        raise ResolutionError(
            f"{edition_id}: technical route must be isolated from legacy home"
        )

    peer = "eda" if edition_id == "ai" else "ai"
    required_fallbacks = TECHNICAL_FALLBACKS | {f"editions/{peer}"}
    if set(config["forbidden_fallbacks"]) != required_fallbacks:
        raise ResolutionError(
            f"{edition_id}: forbidden_fallbacks must reject newsroom and peer edition"
        )
    for key in ("workspace", "editorial_profile", "sources"):
        parts = PurePosixPath(paths[key]).parts
        if parts[:2] != ("editions", edition_id):
            raise ResolutionError(
                f"{edition_id}: technical newsroom fallback is forbidden: "
                f"{key}={paths[key]}"
            )


def _normalize_repository_path(
    label: str,
    raw_path: str,
    repo_root: Path,
    *,
    expected_kind: Optional[str],
    access: str,
) -> Mapping[str, Any]:
    relative = PurePosixPath(raw_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ResolutionError(
            f"{label}: path escapes repository: {raw_path!r}"
        )
    root = repo_root.resolve()
    candidate = repo_root.joinpath(*relative.parts)
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ResolutionError(
            f"{label}: resolved path escapes repository: {raw_path!r}"
        ) from error

    exists = resolved.exists()
    if expected_kind is not None:
        if not exists:
            raise ResolutionError(
                f"{label}: required input is missing: {raw_path}"
            )
        if expected_kind == "file" and not resolved.is_file():
            raise ResolutionError(
                f"{label}: expected file: {raw_path}"
            )
        if expected_kind == "directory" and not resolved.is_dir():
            raise ResolutionError(
                f"{label}: expected directory: {raw_path}"
            )
    if expected_kind is not None:
        normalized_kind = expected_kind
    elif exists and resolved.is_dir():
        normalized_kind = "directory"
    else:
        normalized_kind = "future-directory"
    return {
        "relative": relative.as_posix(),
        "absolute": str(resolved),
        "exists": exists,
        "kind": normalized_kind,
        "access": access,
    }


def _phase_plan(
    edition_id: str, config: Mapping[str, Any]
) -> Sequence[Mapping[str, Any]]:
    if edition_id == "current-affairs":
        later_mode = "delegated-to-legacy-wrapper-not-executed"
    else:
        later_mode = "disabled-in-stage-1"
    phases = [
        {
            "phase": "resolve",
            "mode": "read-only",
            "executed": True,
            "writes": [],
        }
    ]
    for phase in ("acquire", "analyze", "decide", "validate", "stage"):
        phases.append(
            {
                "phase": phase,
                "mode": later_mode,
                "executed": False,
                "writes": [],
            }
        )
    if edition_id == "current-affairs":
        phases[-1]["declared_entrypoint"] = config["paths"][
            "legacy_entrypoint"
        ]
    else:
        phases[-1]["release_mode"] = config["release"]["mode"]
        phases[-1]["requires_human_approval"] = True
    return phases


def resolve_requested(
    edition_id: str,
    repo_root: Path = REPO_ROOT,
    configs: Optional[Mapping[str, Mapping[str, Any]]] = None,
) -> Mapping[str, Any]:
    if edition_id not in CONFIG_PATHS:
        raise ResolutionError(f"unknown edition: {edition_id}")
    try:
        schema = load_json(repo_root / "editions/_schema/runtime-edition.schema.json")
    except EditionValidationError as error:
        raise ResolutionError(str(error)) from error
    loaded = load_runtime_configs() if configs is None else dict(configs)
    resolved = validate_and_resolve_all(loaded, schema, repo_root)
    result = dict(resolved[edition_id])
    result["config"] = (
        Path("editions") / edition_id / "runtime.json"
    ).as_posix()
    result["route_contract"] = {
        "legacy_inventory": "tests/fixtures/legacy-routes.json",
        "excluded_inventory": "tests/fixtures/excluded-content.json",
    }
    return {
        "status": "passed",
        "mode": "resolve-only",
        "edition": edition_id,
        "resolution": result,
        "side_effects": [],
        "workflow_executed": False,
        "content_written": False,
        "git_written": False,
    }


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--edition", required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] = ()) -> int:
    arguments = _parse_args(argv)
    try:
        report = resolve_requested(arguments.edition)
    except ResolutionError as error:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "mode": "resolve-only",
                    "edition": arguments.edition,
                    "error": str(error),
                    "side_effects": [],
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
