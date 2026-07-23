from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_change_scope.py"


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)


class VerifyChangeScopeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.repo = Path(self.tempdir.name)
        run(["git", "init", "-q"], self.repo)
        run(["git", "config", "user.email", "test@example.com"], self.repo)
        run(["git", "config", "user.name", "Test"], self.repo)

        (self.repo / "src").mkdir()
        (self.repo / "migrations").mkdir()
        (self.repo / "src" / "app.py").write_text("value = 1\n", encoding="utf-8")
        (self.repo / "README.md").write_text("baseline\n", encoding="utf-8")
        (self.repo / "migrations" / "001.sql").write_text("baseline\n", encoding="utf-8")
        run(["git", "add", "."], self.repo)
        committed = run(["git", "commit", "-qm", "baseline"], self.repo)
        self.assertEqual(committed.returncode, 0, committed.stderr)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def check_scope(self, *args: str) -> subprocess.CompletedProcess[str]:
        return run(["python", str(SCRIPT), "--repo", str(self.repo), *args], self.repo)

    def reset(self) -> None:
        run(["git", "reset", "--hard", "-q", "HEAD"], self.repo)
        run(["git", "clean", "-fdq"], self.repo)

    def test_allowed_modification_passes(self) -> None:
        (self.repo / "src" / "app.py").write_text("value = 2\n", encoding="utf-8")
        result = self.check_scope("--allow", "src/**")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_outside_allowlist_fails(self) -> None:
        (self.repo / "README.md").write_text("changed\n", encoding="utf-8")
        result = self.check_scope("--allow", "src/**")
        self.assertEqual(result.returncode, 1)
        self.assertIn("README.md", result.stderr)

    def test_denied_modification_fails(self) -> None:
        (self.repo / "migrations" / "001.sql").write_text("changed\n", encoding="utf-8")
        result = self.check_scope("--allow", "**", "--deny", "migrations/**")
        self.assertEqual(result.returncode, 1)
        self.assertIn("migrations/001.sql", result.stderr)

    def test_denied_deletion_fails(self) -> None:
        (self.repo / "migrations" / "001.sql").unlink()
        result = self.check_scope("--allow", "**", "--deny", "migrations/**")
        self.assertEqual(result.returncode, 1)
        self.assertIn("migrations/001.sql", result.stderr)

    def test_denied_untracked_file_fails(self) -> None:
        (self.repo / "migrations" / "002.sql").write_text("new\n", encoding="utf-8")
        result = self.check_scope("--allow", "**", "--deny", "migrations/**")
        self.assertEqual(result.returncode, 1)
        self.assertIn("migrations/002.sql", result.stderr)

    def test_rename_checks_old_and_new_paths(self) -> None:
        (self.repo / "src" / "moved.sql").write_text(
            (self.repo / "migrations" / "001.sql").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        (self.repo / "migrations" / "001.sql").unlink()
        run(["git", "add", "-A"], self.repo)
        result = self.check_scope("--allow", "src/**", "--deny", "migrations/**")
        self.assertEqual(result.returncode, 1)
        self.assertIn("migrations/001.sql", result.stderr)

    def test_tracked_whitespace_error_fails(self) -> None:
        (self.repo / "src" / "app.py").write_text("value = 2   \n", encoding="utf-8")
        result = self.check_scope("--allow", "src/**")
        self.assertEqual(result.returncode, 1)
        self.assertIn("trailing whitespace", result.stderr)

    def test_new_repository_without_head_is_supported(self) -> None:
        other = Path(self.tempdir.name) / "fresh"
        other.mkdir()
        run(["git", "init", "-q"], other)
        (other / "src").mkdir()
        (other / "src" / "new.py").write_text("value = 1\n", encoding="utf-8")
        result = run(
            ["python", str(SCRIPT), "--repo", str(other), "--allow", "src/**"],
            other,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("empty tree", result.stdout)


if __name__ == "__main__":
    unittest.main()
