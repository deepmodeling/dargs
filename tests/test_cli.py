from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

this_directory = Path(__file__).parent


class TestCli(unittest.TestCase):
    def test_check(self) -> None:
        subprocess.check_call(
            [
                "dargs",
                "check",
                "-f",
                "dargs._test.test_arguments",
                str(this_directory / "test_arguments.json"),
                str(this_directory / "test_arguments.json"),
            ]
        )
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "dargs",
                "check",
                "-f",
                "dargs._test.test_arguments",
                str(this_directory / "test_arguments.json"),
                str(this_directory / "test_arguments.json"),
            ]
        )
        with (this_directory / "test_arguments.json").open() as f:
            subprocess.check_call(
                [
                    "dargs",
                    "check",
                    "-f",
                    "dargs._test.test_arguments",
                ],
                stdin=f,
            )

    def test_doc_all_arguments(self) -> None:
        """Test printing documentation for all arguments."""
        result = subprocess.run(
            [
                "dargs",
                "doc",
                "dargs._test.test_arguments",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        # Check that all arguments are in the output (including nested base)
        self.assertIn("test1:", result.stdout)
        self.assertIn("test2:", result.stdout)
        self.assertIn("test3:", result.stdout)
        self.assertIn("base:", result.stdout)
        self.assertIn("Argument 1", result.stdout)
        self.assertIn("Argument 2", result.stdout)
        self.assertIn("Argument 3", result.stdout)

    def test_doc_specific_argument(self) -> None:
        """Test printing documentation for a specific argument."""
        result = subprocess.run(
            [
                "dargs",
                "doc",
                "dargs._test.test_arguments",
                "test1",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        # Check that only test1 is in the output
        self.assertIn("test1:", result.stdout)
        self.assertIn("Argument 1", result.stdout)
        # test2 and test3 should not be in the output
        self.assertNotIn("Argument 2", result.stdout)
        self.assertNotIn("Argument 3", result.stdout)

    def test_doc_nested_arguments(self) -> None:
        """Test printing documentation for nested arguments."""
        # Test top-level base argument
        result = subprocess.run(
            [
                "dargs",
                "doc",
                "dargs._test.test_arguments",
                "base",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("base:", result.stdout)
        self.assertIn("sub1:", result.stdout)
        self.assertIn("sub2:", result.stdout)
        self.assertIn("subsub1:", result.stdout)

        # Test specific nested path
        result = subprocess.run(
            [
                "dargs",
                "doc",
                "dargs._test.test_arguments",
                "base/sub1",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("sub1:", result.stdout)
        self.assertIn("Sub argument 1", result.stdout)
        # Check that the full path is in the output
        self.assertIn("base/sub1", result.stdout)
        # subsub1 should not be in the output
        self.assertNotIn("subsub1:", result.stdout)

        # Test deeply nested path
        result = subprocess.run(
            [
                "dargs",
                "doc",
                "dargs._test.test_arguments",
                "base/sub2/subsub1",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("subsub1:", result.stdout)
        self.assertIn("Sub-sub argument 1", result.stdout)
        # Check that the full path is in the output
        self.assertIn("base/sub2/subsub1", result.stdout)

    def test_doc_invalid_path(self) -> None:
        """Test error handling for invalid argument path."""
        result = subprocess.run(
            [
                "dargs",
                "doc",
                "dargs._test.test_arguments",
                "invalid",
            ],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not found", result.stderr)

    def test_doc_invalid_nested_path(self) -> None:
        """Test error handling for invalid nested argument path."""
        result = subprocess.run(
            [
                "dargs",
                "doc",
                "dargs._test.test_arguments",
                "base/invalid",
            ],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not found", result.stderr)

    def test_doc_with_python_module(self) -> None:
        """Test doc command using python -m."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "dargs",
                "doc",
                "dargs._test.test_arguments",
                "test1",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertIn("test1:", result.stdout)
        self.assertIn("Argument 1", result.stdout)

    def test_doc_invalid_function_format(self) -> None:
        """Test error handling for invalid function format."""
        result = subprocess.run(
            [
                "dargs",
                "doc",
                "invalid_func",
            ],
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("module.function", result.stderr)
