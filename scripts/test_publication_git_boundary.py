#!/usr/bin/env python3
"""Regression tests for the dedicated publication checkout Git boundary."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = (
    "publication-git-preflight.sh",
    "finalize-publication.sh",
)


def run(*args: str, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        check=check,
        capture_output=True,
        text=True,
    )


class PublicationGitBoundaryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.origin = self.root / "origin.git"
        self.seed = self.root / "seed"
        self.publisher = self.root / "publisher"

        run("git", "init", "--bare", str(self.origin), cwd=self.root)
        run("git", "init", "-b", "main", str(self.seed), cwd=self.root)
        run("git", "config", "user.name", "test desk", cwd=self.seed)
        run("git", "config", "user.email", "desk@example.test", cwd=self.seed)
        (self.seed / "scripts").mkdir()
        for name in SCRIPTS:
            shutil.copy2(ROOT / "scripts" / name, self.seed / "scripts" / name)
            os.chmod(self.seed / "scripts" / name, 0o755)
        (self.seed / "README.md").write_text("seed\n", encoding="utf-8")
        run("git", "add", ".", cwd=self.seed)
        run("git", "commit", "-m", "seed", cwd=self.seed)
        run("git", "remote", "add", "origin", str(self.origin), cwd=self.seed)
        run("git", "push", "-u", "origin", "main", cwd=self.seed)
        run(
            "git",
            f"--git-dir={self.origin}",
            "symbolic-ref",
            "HEAD",
            "refs/heads/main",
            cwd=self.root,
        )

        run("git", "clone", str(self.origin), str(self.publisher), cwd=self.root)
        run("git", "config", "user.name", "test desk", cwd=self.publisher)
        run("git", "config", "user.email", "desk@example.test", cwd=self.publisher)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_preflight_rejects_dirty_publication_checkout(self) -> None:
        (self.publisher / "README.md").write_text("dirty\n", encoding="utf-8")
        completed = run(
            "bash",
            "scripts/publication-git-preflight.sh",
            cwd=self.publisher,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("dirty checkout", completed.stderr)

    def test_current_affairs_finalizer_pushes_only_allowed_content(self) -> None:
        article = self.publisher / "content/2026-08-04/article.md"
        article.parent.mkdir(parents=True)
        article.write_text(
            '---\ntitle: "test"\ndate: 2026-08-04\n---\n\nbody\n',
            encoding="utf-8",
        )
        completed = run(
            "bash",
            "scripts/finalize-publication.sh",
            "current-affairs",
            "2026-08-04",
            cwd=self.publisher,
        )
        commit_sha = completed.stdout.strip()
        self.assertRegex(commit_sha, r"^[0-9a-f]{40}$")
        remote_article = run(
            "git",
            f"--git-dir={self.origin}",
            "show",
            "main:content/2026-08-04/article.md",
            cwd=self.root,
        )
        self.assertIn("body", remote_article.stdout)
        self.assertEqual(run("git", "status", "--porcelain", cwd=self.publisher).stdout, "")

    def test_finalizer_rejects_unrelated_dirty_file(self) -> None:
        article = self.publisher / "content/2026-08-04/article.md"
        article.parent.mkdir(parents=True)
        article.write_text("article\n", encoding="utf-8")
        (self.publisher / "README.md").write_text("unexpected\n", encoding="utf-8")
        before = run(
            "git", f"--git-dir={self.origin}", "rev-parse", "main", cwd=self.root
        ).stdout
        completed = run(
            "bash",
            "scripts/finalize-publication.sh",
            "current-affairs",
            "2026-08-04",
            cwd=self.publisher,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("unrelated change", completed.stderr)
        after = run(
            "git", f"--git-dir={self.origin}", "rev-parse", "main", cwd=self.root
        ).stdout
        self.assertEqual(before, after)

    def test_ai_finalizer_rejects_extra_file_inside_date_roots(self) -> None:
        article_root = self.publisher / "content/ai/2026-08-04"
        decision_root = self.publisher / "decisions/ai/2026-08-04"
        article_root.mkdir(parents=True)
        decision_root.mkdir(parents=True)
        (article_root / "article.md").write_text("article\n", encoding="utf-8")
        (article_root / "unexpected.txt").write_text("extra\n", encoding="utf-8")
        (decision_root / "evidence.json").write_text("{}\n", encoding="utf-8")
        (decision_root / "release.json").write_text("{}\n", encoding="utf-8")
        completed = run(
            "bash",
            "scripts/finalize-publication.sh",
            "ai",
            "2026-08-04",
            cwd=self.publisher,
            check=False,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("exactly", completed.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
