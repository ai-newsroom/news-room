import hashlib
import json
import os
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

import worktree_manifest


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "worktree-manifest-cases.json"


class WorktreeManifestTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name) / "fixture repo with spaces"
        self.repo.mkdir()
        self.git("init", "--quiet")
        initial = self.fixture["initial"]
        for path, content in initial["staged_files"].items():
            self.write(path, content)
        self.git("add", "--", *initial["staged_files"].keys())
        for path, content in initial["worktree_modifications"].items():
            self.write(path, content)
        for path, content in initial["untracked_files"].items():
            self.write(path, content)

    def tearDown(self):
        self.temporary.cleanup()

    def git(self, *args):
        environment = os.environ.copy()
        environment["GIT_OPTIONAL_LOCKS"] = "0"
        return subprocess.run(
            ["git", "--no-optional-locks", "-C", str(self.repo), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            env=environment,
        )

    def write(self, relative, content):
        path = self.repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def snapshot(self):
        result = {}
        for root, directories, files in os.walk(self.repo, followlinks=False):
            directories.sort()
            files.sort()
            for name in directories + files:
                path = Path(root) / name
                relative = path.relative_to(self.repo).as_posix()
                metadata = os.lstat(path)
                if stat.S_ISREG(metadata.st_mode):
                    digest = hashlib.sha256(path.read_bytes()).hexdigest()
                    kind = "file"
                elif stat.S_ISLNK(metadata.st_mode):
                    digest = hashlib.sha256(os.fsencode(os.readlink(path))).hexdigest()
                    kind = "symlink"
                else:
                    digest = None
                    kind = "directory" if stat.S_ISDIR(metadata.st_mode) else "special"
                result[relative] = {
                    "kind": kind,
                    "mode": stat.S_IMODE(metadata.st_mode),
                    "size": metadata.st_size,
                    "mtime_ns": metadata.st_mtime_ns,
                    "sha256": digest,
                }
        return result

    def test_capture_is_read_only_and_lists_space_and_nested_paths(self):
        before_filesystem = self.snapshot()
        manifest = worktree_manifest.capture(self.repo)
        after_filesystem = self.snapshot()
        self.assertEqual(after_filesystem, before_filesystem)
        self.assertEqual(
            [entry["path"] for entry in manifest["entries"]],
            self.fixture["expected_initial_paths"],
        )
        entries = {entry["path"]: entry for entry in manifest["entries"]}
        self.assertEqual(entries["tracked modified.txt"]["status"], "AM")
        self.assertTrue(entries["tracked modified.txt"]["tracked"])
        self.assertEqual(entries["root untracked.txt"]["status"], "??")
        self.assertFalse(entries["root untracked.txt"]["tracked"])
        self.assertRegex(
            entries["untracked dir/deeper/file one.txt"]["worktree"]["sha256"],
            r"^[0-9a-f]{64}$",
        )

    def test_allowed_nested_new_path_is_reported_separately(self):
        before = worktree_manifest.capture(self.repo)
        case = self.fixture["allowed_new"]
        for path, content in case["files"].items():
            self.write(path, content)
        after = worktree_manifest.capture(self.repo)
        report = worktree_manifest.compare(
            before, after, allowed_new=case["allowances"]
        )
        self.assertEqual(report["status"], "pass")
        self.assertEqual(
            [item["path"] for item in report["allowed_new"]],
            ["allowed new/nested/new file.txt"],
        )
        self.assertEqual(report["unexpected_new"], [])
        self.assertEqual(report["coverage"]["explanation_rate"], 1.0)
        self.assertEqual(
            report["coverage"]["preserved_count"], len(before["entries"])
        )

    def test_unexpected_new_path_fails_comparison(self):
        before = worktree_manifest.capture(self.repo)
        for path, content in self.fixture["unexpected_new"]["files"].items():
            self.write(path, content)
        report = worktree_manifest.compare(
            before, worktree_manifest.capture(self.repo)
        )
        self.assertEqual(report["status"], "fail")
        self.assertEqual(
            [item["path"] for item in report["unexpected_new"]],
            ["surprise/new.txt"],
        )
        self.assertEqual(report["coverage"]["violation_count"], 1)

    def test_changed_preexisting_hash_fails_even_when_git_status_is_same(self):
        before = worktree_manifest.capture(self.repo)
        case = self.fixture["changed_preexisting"]
        self.write(case["path"], case["replacement"])
        report = worktree_manifest.compare(
            before, worktree_manifest.capture(self.repo)
        )
        self.assertEqual(report["status"], "fail")
        self.assertEqual(
            [item["path"] for item in report["preexisting_changed"]],
            [case["path"]],
        )
        self.assertIn(
            "worktree", report["preexisting_changed"][0]["changed_fields"]
        )

    def test_missing_preexisting_path_fails_comparison(self):
        before = worktree_manifest.capture(self.repo)
        path = self.fixture["missing_preexisting"]["path"]
        (self.repo / path).unlink()
        report = worktree_manifest.compare(
            before, worktree_manifest.capture(self.repo)
        )
        self.assertEqual(report["status"], "fail")
        self.assertEqual(
            [item["path"] for item in report["preexisting_missing"]], [path]
        )

    def test_index_change_is_detected_without_worktree_content_change(self):
        before = worktree_manifest.capture(self.repo)
        self.git("add", "--", "tracked modified.txt")
        report = worktree_manifest.compare(
            before, worktree_manifest.capture(self.repo)
        )
        changed = next(
            item
            for item in report["preexisting_changed"]
            if item["path"] == "tracked modified.txt"
        )
        self.assertEqual(report["status"], "fail")
        self.assertIn("status", changed["changed_fields"])
        self.assertIn("index", changed["changed_fields"])

    def test_exact_allowance_does_not_authorize_sibling(self):
        before = worktree_manifest.capture(self.repo)
        self.write("allowed.txt", "yes\n")
        self.write("allowed.txt.sibling", "no\n")
        report = worktree_manifest.compare(
            before,
            worktree_manifest.capture(self.repo),
            allowed_new=["allowed.txt"],
        )
        self.assertEqual(report["status"], "fail")
        self.assertEqual(
            [item["path"] for item in report["allowed_new"]], ["allowed.txt"]
        )
        self.assertEqual(
            [item["path"] for item in report["unexpected_new"]],
            ["allowed.txt.sibling"],
        )

    def test_unsafe_allowance_is_rejected(self):
        manifest = worktree_manifest.capture(self.repo)
        for allowance in ("../outside", ".git/", "/absolute"):
            with self.subTest(allowance=allowance):
                with self.assertRaises(worktree_manifest.ManifestError):
                    worktree_manifest.compare(
                        manifest, manifest, allowed_new=[allowance]
                    )

    def test_compare_live_cli_is_read_only_and_returns_json(self):
        before = worktree_manifest.capture(self.repo)
        manifest_path = Path(self.temporary.name) / "pre manifest.json"
        manifest_path.write_text(
            json.dumps(before, ensure_ascii=True), encoding="utf-8"
        )
        before_filesystem = self.snapshot()
        result = subprocess.run(
            [
                "python3",
                str(Path(worktree_manifest.__file__)),
                "compare-live",
                "--repo",
                str(self.repo),
                "--before",
                str(manifest_path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        output = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assertEqual(output["comparison"]["status"], "pass")
        self.assertEqual(
            output["after_manifest"]["summary"]["entry_count"],
            len(before["entries"]),
        )
        self.assertEqual(self.snapshot(), before_filesystem)


if __name__ == "__main__":
    unittest.main(verbosity=2)
