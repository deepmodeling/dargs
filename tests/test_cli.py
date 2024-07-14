from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

this_directory = Path(__file__).parent


class TestCli(unittest.TestCase):
    def test_check(self):
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
