import os
import subprocess
import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class MenuTests(unittest.TestCase):
    def test_invalid_choice_repeats_menu_until_exit(self):
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "src" / "init.py")],
            input="wrong\n4\n",
            text=True,
            capture_output=True,
            cwd=PROJECT_ROOT,
            check=False,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("Welcome to Skooly", result.stdout)
        self.assertIn("Choose 1-4", result.stdout)
        self.assertIn("Please choose 1, 2, 3, or 4", result.stdout)
        self.assertIn("Goodbye", result.stdout)
        self.assertEqual(result.stdout.count("1. Search books"), 2)

    def test_title_search_displays_real_catalogue_result(self):
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "src" / "init.py")],
            input="1\npYtHoN\n\n\n\n4\n",
            text=True,
            capture_output=True,
            cwd=PROJECT_ROOT,
            env={**os.environ, "SKOOLY_DATABASE_URL": "dbname=skooly"},
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("SK-005", result.stdout)
        self.assertIn("Clean Code in Python", result.stdout)
        self.assertIn("Goodbye", result.stdout)


if __name__ == "__main__":
    unittest.main()
