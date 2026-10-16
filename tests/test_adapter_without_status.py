from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "fullstack-orchestrator" / "scripts"


class AdapterWithoutStatusTests(unittest.TestCase):
    def _bootstrap(self, seed: Path, adapter: Path, *options: str) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "bootstrap_project_adapter.py"),
                str(seed),
                "--project-name", "Test Project",
                "--coordinator", str(adapter),
                "--runbooks", "none",
                "--write",
                *options,
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        return result

    def test_fresh_bootstrap_validates_without_status(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            seed = root / "seed"
            seed.mkdir()
            adapter = root / "adapter"

            scan = self._bootstrap(seed, adapter)

            self.assertFalse((adapter / "STATUS.md").exists())
            self.assertNotIn("STATUS.md", scan.stdout)
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "validate_project_adapter.py"), str(adapter)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_bootstrap_rerun_preserves_existing_status_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            seed = root / "seed"
            seed.mkdir()
            adapter = root / "adapter"
            self._bootstrap(seed, adapter)
            legacy = adapter / "STATUS.md"
            original = b"# Project-owned history\r\n\r\nCaf\xc3\xa9 gate pending.\r\n"
            legacy.write_bytes(original)

            self._bootstrap(seed, adapter, "--force")

            self.assertEqual(original, legacy.read_bytes())
            result = subprocess.run(
                [sys.executable, str(SCRIPTS / "validate_project_adapter.py"), str(adapter)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertEqual(original, legacy.read_bytes())


if __name__ == "__main__":
    unittest.main()
