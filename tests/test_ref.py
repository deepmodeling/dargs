"""Tests for $ref loading from external JSON/YAML files."""

from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest

from dargs import Argument


class TestRef(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        import shutil

        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def _tmpfile(self, name: str) -> str:
        return os.path.join(self._tmpdir, name)

    def _write_json(self, name: str, data: dict) -> str:
        path = self._tmpfile(name)
        with open(path, "w") as f:
            json.dump(data, f)
        return path

    def _write_yaml(self, name: str, text: str) -> str:
        path = self._tmpfile(name)
        with open(path, "w") as f:
            f.write(text)
        return path

    def test_ref_not_allowed_by_default(self) -> None:
        """$ref raises ValueError when allow_ref is not set (secure by default)."""
        ref_path = self._write_json("ref_default.json", {"sub1": 1})
        ca = Argument("base", dict, [Argument("sub1", int)])
        with self.assertRaises(ValueError):
            ca.check({"base": {"$ref": ref_path}})
        with self.assertRaises(ValueError):
            ca.normalize({"base": {"$ref": ref_path}})
        with self.assertRaises(ValueError):
            ca.check_value({"$ref": ref_path})
        with self.assertRaises(ValueError):
            ca.normalize_value({"$ref": ref_path})

    def test_ref_json_check(self) -> None:
        """$ref to a JSON file is resolved before check."""
        ref_path = self._write_json("ref_test.json", {"sub1": 1, "sub2": "hello"})
        ca = Argument(
            "base",
            dict,
            [
                Argument("sub1", int),
                Argument("sub2", str),
            ],
        )
        ca.check({"base": {"$ref": ref_path}}, allow_ref=True)

    def test_ref_json_normalize(self) -> None:
        """$ref to a JSON file is resolved before normalize."""
        ref_path = self._write_json("ref_norm.json", {"sub1": 1})
        ca = Argument(
            "base",
            dict,
            [
                Argument("sub1", int),
                Argument("sub2", str, optional=True, default="default"),
            ],
        )
        result = ca.normalize({"base": {"$ref": ref_path}}, allow_ref=True)
        self.assertEqual(result["base"]["sub1"], 1)
        self.assertEqual(result["base"]["sub2"], "default")

    def test_ref_local_override(self) -> None:
        """Keys in the dict alongside $ref override keys from the loaded file."""
        ref_path = self._write_json(
            "ref_override.json", {"sub1": 1, "sub2": "from_file"}
        )
        ca = Argument(
            "base",
            dict,
            [
                Argument("sub1", int),
                Argument("sub2", str),
            ],
        )
        result = ca.normalize(
            {"base": {"$ref": ref_path, "sub2": "local"}}, allow_ref=True
        )
        self.assertEqual(result["base"]["sub1"], 1)
        self.assertEqual(result["base"]["sub2"], "local")

    def test_ref_yaml(self) -> None:
        """$ref to a YAML file is resolved when pyyaml is installed."""
        if importlib.util.find_spec("yaml") is None:
            self.skipTest("pyyaml not installed")
        ref_path = self._write_yaml("ref_test.yaml", "sub1: 42\nsub2: yaml_val\n")
        ca = Argument(
            "base",
            dict,
            [
                Argument("sub1", int),
                Argument("sub2", str),
            ],
        )
        ca.check({"base": {"$ref": ref_path}}, allow_ref=True)

    def test_ref_yml_extension(self) -> None:
        """$ref works with .yml extension as well."""
        if importlib.util.find_spec("yaml") is None:
            self.skipTest("pyyaml not installed")
        ref_path = self._write_yaml("ref_test.yml", "sub1: 7\nsub2: yml_val\n")
        ca = Argument(
            "base",
            dict,
            [
                Argument("sub1", int),
                Argument("sub2", str),
            ],
        )
        ca.check({"base": {"$ref": ref_path}}, allow_ref=True)

    def test_ref_unsupported_extension(self) -> None:
        """$ref with unsupported extension raises ValueError."""
        ref_path = self._tmpfile("ref_test.toml")
        with open(ref_path, "w") as f:
            f.write("sub1 = 1\n")
        ca = Argument("base", dict, [Argument("sub1", int)])
        with self.assertRaises(ValueError):
            ca.check({"base": {"$ref": ref_path}}, allow_ref=True)

    def test_ref_check_value(self) -> None:
        """$ref is resolved when using check_value."""
        ref_path = self._write_json("ref_val.json", {"sub1": 5, "sub2": "v"})
        ca = Argument(
            "base",
            dict,
            [
                Argument("sub1", int),
                Argument("sub2", str),
            ],
        )
        ca.check_value({"$ref": ref_path}, allow_ref=True)

    def test_ref_normalize_value(self) -> None:
        """$ref is resolved when using normalize_value."""
        ref_path = self._write_json("ref_normval.json", {"sub1": 99})
        ca = Argument(
            "base",
            dict,
            [
                Argument("sub1", int),
                Argument("sub2", str, optional=True, default="d"),
            ],
        )
        result = ca.normalize_value({"$ref": ref_path}, allow_ref=True)
        self.assertEqual(result["sub1"], 99)
        self.assertEqual(result["sub2"], "d")


if __name__ == "__main__":
    unittest.main()
