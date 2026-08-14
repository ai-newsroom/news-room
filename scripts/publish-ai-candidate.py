#!/usr/bin/env python3
"""Validate and materialize one automatically authorized AI article.

This command deliberately stops before Git, push, and deployment.  It is the
deterministic repository-write boundary used by the scheduled Codex task,
which performs those external actions only after this command and the full
site test suite succeed in an isolated clean worktree.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
AUTOMATIC_POLICY_ID = "ai-auto-publish-v1"
SPECIAL_POLICY_ID = "ai-special-publish-v1"
# Backwards-compatible name used by the existing tests and callers.
POLICY_ID = AUTOMATIC_POLICY_ID
SEOUL = ZoneInfo("Asia/Seoul")
PUBLICATION_ID = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2})(?:--(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*))?$"
)
EVIDENCE_ORDER = {"E0": 0, "E1": 1, "E2": 2, "E3": 3, "E4": 4}
REQUIRED_HEADINGS = (
    "## 이해상충과 취재 조건",
    "## 근거 원장",
    "## 출처",
)
ARTICLE_FRONTMATTER_KEYS = frozenset({
    "edition",
    "decision",
    "title",
    "date",
    "subject",
    "summary",
    "evidence_ceiling",
    "reproducibility",
    "conflicts",
    "publication_kind",
})
REQUIRED_ARTICLE_FRONTMATTER_KEYS = ARTICLE_FRONTMATTER_KEYS - {"publication_kind"}
AUTOMATIC_CHECKS = (
    "ai-editorial-config",
    "article-frontmatter-schema",
    "selection-threshold",
    "central-evidence-e2",
    "ai-technical-blog-v2",
    "claim-source-ledger",
    "publication-id-and-route-unique",
    "artifact-hashes",
    "site-tests-and-build",
)

sys.path.insert(0, str(ROOT / "editions/ai/editorial"))
import style_v2  # noqa: E402


class PublishError(ValueError):
    """A candidate is not safe to materialize."""


def publication_identity(publication_id: str) -> tuple[str, str, str | None]:
    match = PUBLICATION_ID.fullmatch(publication_id)
    if match is None:
        raise PublishError(
            "publication id must be YYYY-MM-DD or YYYY-MM-DD--lowercase-slug"
        )
    publication_date = match.group("date")
    slug = match.group("slug")
    kind = "special" if slug else "regular"
    return publication_date, kind, slug


def publication_route(publication_id: str) -> str:
    publication_date, kind, slug = publication_identity(publication_id)
    if kind == "special":
        return f"/ai/{publication_date}/{slug}/"
    return f"/ai/{publication_date}/"


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PublishError(f"invalid JSON: {path}") from error


def regular_file_below(path: Path, root: Path) -> Path:
    resolved_root = root.resolve()
    resolved = path.resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as error:
        raise PublishError(f"path escapes allowed root: {path}") from error
    if path.is_symlink() or not resolved.is_file():
        raise PublishError(f"regular file required: {path}")
    return resolved


def parse_frontmatter(text: str) -> Mapping[str, str]:
    if not text.startswith("---\n"):
        raise PublishError("article frontmatter missing")
    marker = text.find("\n---\n", 4)
    if marker < 0:
        raise PublishError("article frontmatter is not closed")
    result: dict[str, str] = {}
    for line in text[4:marker].splitlines():
        if ":" not in line:
            continue
        key, raw = line.split(":", 1)
        key = key.strip()
        if not key:
            raise PublishError("article frontmatter key is empty")
        if key in result:
            raise PublishError(f"duplicate article frontmatter field: {key}")
        value = raw.strip()
        if value.startswith('"') and value.endswith('"'):
            try:
                value = json.loads(value)
            except json.JSONDecodeError as error:
                raise PublishError(f"invalid frontmatter string: {key}") from error
        result[key] = str(value)
    return result


def article_lead(text: str) -> str:
    """Return the first three prose paragraphs before the first article section."""
    marker = text.find("\n---\n", 4)
    if marker < 0:
        raise PublishError("article frontmatter is not closed")
    introduction = text[marker + 5 :].split("\n## ", 1)[0]
    paragraphs = [
        " ".join(line.strip() for line in block.splitlines() if line.strip())
        for block in introduction.split("\n\n")
    ]
    return "\n".join(paragraph for paragraph in paragraphs[:3] if paragraph)


def alignment_terms(
    value: Any,
    *,
    field: str,
    minimum: int,
    maximum: int,
) -> list[str]:
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        raise PublishError(
            f"special brief alignment {field} must contain {minimum} to {maximum} terms"
        )
    terms: list[str] = []
    for item in value:
        if not isinstance(item, str) or len(item.strip()) < 2:
            raise PublishError(
                f"special brief alignment {field} requires non-empty text terms"
            )
        terms.append(item.strip())
    if len({term.casefold() for term in terms}) != len(terms):
        raise PublishError(f"special brief alignment {field} contains duplicates")
    return terms


def validate_special_brief_alignment(
    evidence: Mapping[str, Any],
    frontmatter: Mapping[str, str],
    article_text: str,
) -> dict[str, Any]:
    """Require a special article's early narrative to preserve the editor's angle."""
    alignment = evidence.get("editorial_brief_alignment")
    if not isinstance(alignment, dict):
        raise PublishError("special brief alignment record is required")
    requested_angle = alignment.get("requested_angle")
    if not isinstance(requested_angle, str) or len(requested_angle.strip()) < 12:
        raise PublishError("special brief alignment requested_angle is required")
    focus_terms = alignment_terms(
        alignment.get("required_focus_terms"),
        field="required_focus_terms",
        minimum=2,
        maximum=8,
    )
    secondary_terms = alignment_terms(
        alignment.get("secondary_terms", []),
        field="secondary_terms",
        minimum=0,
        maximum=8,
    )
    if {term.casefold() for term in focus_terms} & {
        term.casefold() for term in secondary_terms
    }:
        raise PublishError("special brief alignment focus and secondary terms overlap")

    central_claim = evidence.get("central_claim")
    if not isinstance(central_claim, str) or not central_claim.strip():
        raise PublishError("special brief alignment requires evidence central_claim")
    targets = {
        "title": frontmatter.get("title", ""),
        "summary": frontmatter.get("summary", ""),
        "lead": article_lead(article_text),
        "central_claim": central_claim,
    }
    normalized_focus = [term.casefold() for term in focus_terms]
    for target, text in targets.items():
        folded = text.casefold()
        if not any(term in folded for term in normalized_focus):
            raise PublishError(
                f"special brief alignment focus is missing from {target}"
            )

    combined = "\n".join(targets.values()).casefold()
    missing_focus = [
        term for term in focus_terms if term.casefold() not in combined
    ]
    if missing_focus:
        raise PublishError(
            "special brief alignment terms are absent from checked targets: "
            + ", ".join(missing_focus)
        )
    focus_hits = sum(combined.count(term) for term in normalized_focus)
    secondary_hits = sum(
        combined.count(term.casefold()) for term in secondary_terms
    )
    if focus_hits <= secondary_hits:
        raise PublishError(
            "special brief alignment is dominated by secondary context"
        )
    return {
        "requested_angle": requested_angle.strip(),
        "required_focus_terms": focus_terms,
        "secondary_terms": secondary_terms,
        "checked_targets": list(targets),
        "focus_hits": focus_hits,
        "secondary_hits": secondary_hits,
        "status": "passed",
    }


def central_claims(evidence: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    claims = evidence.get("claims")
    if not isinstance(claims, list) or not claims:
        raise PublishError("evidence claims are required")
    central = [
        claim for claim in claims
        if isinstance(claim, dict) and claim.get("central") is True
    ]
    if not central:
        raise PublishError("at least one central claim is required")
    return central


def validate_sources(claims: list[Mapping[str, Any]]) -> None:
    urls: set[str] = set()
    for claim in claims:
        sources = claim.get("sources")
        if not isinstance(sources, list) or not sources:
            raise PublishError("every central claim requires sources")
        for source in sources:
            if not isinstance(source, dict):
                raise PublishError("claim source must be an object")
            url = source.get("url")
            grade = source.get("source_grade")
            source_type = source.get("source_type")
            if grade is None:
                grade = source_type
            elif source_type is not None and source_type != grade:
                raise PublishError("claim source grade fields conflict")
            if (
                not isinstance(url, str)
                or not url.startswith("https://")
                or grade not in {"P0", "P1", "P2", "I1", "S1", "S2"}
            ):
                raise PublishError("claim source URL or grade is invalid")
            urls.add(url)
    if len(urls) < 2:
        raise PublishError("automatic publication requires at least two source URLs")


def validate_candidate(
    article_path: Path,
    evidence_path: Path,
    publication_id: str,
    *,
    repo_root: Path = ROOT,
    require_today: bool = True,
    publication_kind: str = "regular",
    approved_by: str | None = None,
    approval_basis: str | None = None,
) -> dict[str, Any]:
    publication_date, identity_kind, _ = publication_identity(publication_id)
    if publication_kind not in {"regular", "special"}:
        raise PublishError("publication kind must be regular or special")
    if identity_kind != publication_kind:
        raise PublishError("publication id and publication kind do not match")
    if require_today and publication_date != datetime.now(SEOUL).date().isoformat():
        raise PublishError("publication id must equal today's Seoul date")
    if publication_kind == "special" and (
        not approved_by or not approved_by.strip()
        or not approval_basis or not approval_basis.strip()
    ):
        raise PublishError("special publication requires explicit approval metadata")

    run_root = repo_root / "var/runs/ai"
    article_path = regular_file_below(article_path, run_root)
    evidence_path = regular_file_below(evidence_path, run_root)
    article_bytes = article_path.read_bytes()
    evidence_bytes = evidence_path.read_bytes()
    article_text = article_bytes.decode("utf-8")
    frontmatter = parse_frontmatter(article_text)
    evidence = load_json(evidence_path)
    if not isinstance(evidence, dict):
        raise PublishError("evidence must be an object")

    frontmatter_keys = set(frontmatter)
    unexpected_fields = sorted(frontmatter_keys - ARTICLE_FRONTMATTER_KEYS)
    missing_fields = sorted(REQUIRED_ARTICLE_FRONTMATTER_KEYS - frontmatter_keys)
    if unexpected_fields:
        raise PublishError(
            "unexpected article frontmatter field(s): "
            + ", ".join(unexpected_fields)
        )
    if missing_fields:
        raise PublishError(
            "missing article frontmatter field(s): " + ", ".join(missing_fields)
        )

    if (
        frontmatter.get("edition") != "ai"
        or frontmatter.get("decision") != "publish-candidate"
        or frontmatter.get("date") != publication_date
    ):
        raise PublishError("article edition, decision, or date is invalid")
    article_kind = frontmatter.get("publication_kind", "regular")
    if article_kind != publication_kind:
        raise PublishError("article publication kind is invalid")
    for field in ("title", "subject", "summary"):
        if not frontmatter[field].strip():
            raise PublishError(f"article {field} is required")
    if frontmatter["reproducibility"] not in {"R0", "R1", "R2", "R3"}:
        raise PublishError("article reproducibility is invalid")
    try:
        article_conflicts = json.loads(frontmatter["conflicts"])
    except json.JSONDecodeError as error:
        raise PublishError("article conflicts must be an inline JSON array") from error
    if (
        not isinstance(article_conflicts, list)
        or not article_conflicts
        or not all(isinstance(item, str) and item.strip() for item in article_conflicts)
    ):
        raise PublishError("article conflicts must contain at least one string")
    evidence_ceiling = frontmatter.get("evidence_ceiling")
    if EVIDENCE_ORDER.get(str(evidence_ceiling), -1) < EVIDENCE_ORDER["E2"]:
        raise PublishError("automatic publication requires E2 or higher")
    if any(heading not in article_text for heading in REQUIRED_HEADINGS):
        raise PublishError("article is missing a required section")
    style_errors = style_v2.validate_text(article_text)
    if style_errors:
        raise PublishError(
            "ai-technical-blog-v2 failed: "
            + json.dumps(style_errors, ensure_ascii=False, sort_keys=True)
        )

    selection = evidence.get("selection")
    if (
        evidence.get("edition") != "ai"
        or evidence.get("date") != publication_date
        or evidence.get("decision") != "publish-candidate"
        or evidence.get("evidence_ceiling") != evidence_ceiling
        or not isinstance(selection, dict)
        or not isinstance(selection.get("total"), int)
        or not isinstance(selection.get("threshold"), int)
        or selection["total"] < selection["threshold"]
    ):
        raise PublishError("evidence identity, ceiling, or selection gate is invalid")
    if evidence.get("publication_id", publication_id) != publication_id:
        raise PublishError("evidence publication id is invalid")
    if evidence.get("publication_kind", "regular") != publication_kind:
        raise PublishError("evidence publication kind is invalid")

    brief_alignment = None
    if publication_kind == "special":
        brief_alignment = validate_special_brief_alignment(
            evidence,
            frontmatter,
            article_text,
        )

    claims = central_claims(evidence)
    if not any(
        EVIDENCE_ORDER.get(str(claim.get("evidence_level")), -1)
        >= EVIDENCE_ORDER["E2"]
        for claim in claims
    ):
        raise PublishError("a central E2-or-higher claim is required")
    validate_sources(claims)

    release_gate = evidence.get("release_gate")
    if not isinstance(release_gate, dict):
        raise PublishError("release gate is required")
    required_gate = {
        "policy_id": (
            SPECIAL_POLICY_ID if publication_kind == "special" else AUTOMATIC_POLICY_ID
        ),
        "human_approval_required": publication_kind == "special",
        "automatic_publish_allowed": publication_kind == "regular",
        "quality_gate_passed": True,
        "content_promotion_allowed": True,
        "git_write_allowed": True,
        "deploy_allowed": True,
    }
    if any(release_gate.get(key) != value for key, value in required_gate.items()):
        raise PublishError("automatic release gate is not authorized")
    conflicts = evidence.get("conflicts")
    if not isinstance(conflicts, list) or not conflicts:
        raise PublishError("conflict disclosure is required")

    targets = (
        repo_root / f"content/ai/{publication_id}",
        repo_root / f"decisions/ai/{publication_id}",
    )
    if any(path.exists() or path.is_symlink() for path in targets):
        raise PublishError("publication id already exists")

    return {
        "publication_id": publication_id,
        "article_path": article_path,
        "evidence_path": evidence_path,
        "article_bytes": article_bytes,
        "evidence_bytes": evidence_bytes,
        "article_sha256": sha256(article_bytes),
        "evidence_sha256": sha256(evidence_bytes),
        "title": frontmatter.get("title", ""),
        "publication_kind": publication_kind,
        "approved_by": approved_by,
        "approval_basis": approval_basis,
        "editorial_brief_alignment": brief_alignment,
    }


def release_record(candidate: Mapping[str, Any], executor: str) -> dict[str, Any]:
    publication_id = str(candidate["publication_id"])
    publication_kind = str(candidate["publication_kind"])
    authorization: dict[str, Any]
    if publication_kind == "special":
        authorization = {
            "mode": "human",
            "approved": True,
            "approved_at": datetime.now(SEOUL).isoformat(timespec="seconds"),
            "approved_by": str(candidate["approved_by"]),
            "approval_basis": str(candidate["approval_basis"]),
            "scope": [
                f"content/ai/{publication_id}/article.md",
                f"decisions/ai/{publication_id}/evidence.json",
                f"decisions/ai/{publication_id}/release.json",
            ],
        }
    else:
        authorization = {
            "mode": "automatic",
            "policy_id": AUTOMATIC_POLICY_ID,
            "authorized_at": datetime.now(SEOUL).isoformat(timespec="seconds"),
            "executor": executor,
            "checks": list(AUTOMATIC_CHECKS),
        }
    release = {
        "schema_version": 1,
        "edition": "ai",
        "publication_id": publication_id,
        "publication_kind": publication_kind,
        "decision": "publish-candidate",
        "release_status": "approved-for-publication",
        "article_path": f"content/ai/{publication_id}/article.md",
        "evidence_path": f"decisions/ai/{publication_id}/evidence.json",
        "artifact_hashes": {
            "article_sha256": candidate["article_sha256"],
            "evidence_sha256": candidate["evidence_sha256"],
        },
        "routes": ["/ai/", publication_route(publication_id)],
        "authorization": authorization,
    }
    if publication_kind == "special":
        release["editorial_brief_alignment"] = candidate[
            "editorial_brief_alignment"
        ]
    return release


def materialize(
    candidate: Mapping[str, Any],
    *,
    executor: str,
    repo_root: Path = ROOT,
) -> dict[str, Any]:
    publication_id = str(candidate["publication_id"])
    article_root = repo_root / f"content/ai/{publication_id}"
    decision_root = repo_root / f"decisions/ai/{publication_id}"
    release = release_record(candidate, executor)
    created: list[Path] = []
    try:
        article_root.mkdir(parents=True)
        created.append(article_root)
        decision_root.mkdir(parents=True)
        created.append(decision_root)
        (article_root / "article.md").write_bytes(candidate["article_bytes"])
        (decision_root / "evidence.json").write_bytes(candidate["evidence_bytes"])
        (decision_root / "release.json").write_text(
            json.dumps(release, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except Exception:
        for path in reversed(created):
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(path)
        raise
    return {
        "status": "materialized",
        "policy_id": (
            SPECIAL_POLICY_ID
            if candidate["publication_kind"] == "special"
            else AUTOMATIC_POLICY_ID
        ),
        "publication_id": publication_id,
        "article_path": release["article_path"],
        "evidence_path": release["evidence_path"],
        "release_path": f"decisions/ai/{publication_id}/release.json",
        "route": publication_route(publication_id),
        "external_actions": {
            "commit": False,
            "push": False,
            "deploy": False,
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--article", required=True, type=Path)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--publication-id", required=True)
    parser.add_argument(
        "--publication-kind",
        choices=("regular", "special"),
        default="regular",
    )
    parser.add_argument("--approved-by")
    parser.add_argument("--approval-basis")
    parser.add_argument("--executor", default="codex-automation")
    parser.add_argument("--check-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        candidate = validate_candidate(
            args.article,
            args.evidence,
            args.publication_id,
            publication_kind=args.publication_kind,
            approved_by=args.approved_by,
            approval_basis=args.approval_basis,
        )
        if args.check_only:
            result = {
                "status": "validated",
                "policy_id": (
                    SPECIAL_POLICY_ID
                    if args.publication_kind == "special"
                    else AUTOMATIC_POLICY_ID
                ),
                "publication_id": args.publication_id,
                "external_actions": {
                    "content": False,
                    "commit": False,
                    "push": False,
                    "deploy": False,
                },
            }
        else:
            result = materialize(candidate, executor=args.executor)
    except (PublishError, OSError, UnicodeDecodeError) as error:
        print(json.dumps({
            "status": "failed",
            "reason": str(error),
            "external_actions": {
                "content": False,
                "commit": False,
                "push": False,
                "deploy": False,
            },
        }, ensure_ascii=False, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
