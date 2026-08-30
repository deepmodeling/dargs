from __future__ import annotations

import json
import os
import tempfile
import unittest
from xml.etree import ElementTree as ET

from dargs import Argument, Variant

try:
    import IPython  # noqa: F401
except ImportError:
    ipython_installed = False
else:
    ipython_installed = True


@unittest.skipUnless(ipython_installed, "IPython not installed")
class TestNotebook(unittest.TestCase):
    def test_nested_relative_ref_uses_containing_file(self) -> None:
        """Notebook rendering resolves nested refs beside their source file."""
        from dargs.notebook import print_html

        with tempfile.TemporaryDirectory() as tmpdir:
            nested = os.path.join(tmpdir, "nested")
            os.mkdir(nested)
            with open(os.path.join(nested, "inner.json"), "w", encoding="utf-8") as f:
                json.dump({"value": 11}, f)
            outer_path = os.path.join(tmpdir, "outer.json")
            with open(outer_path, "w", encoding="utf-8") as f:
                json.dump({"nested": {"$ref": "nested/inner.json"}}, f)

            argument = Argument(
                "base",
                dict,
                [Argument("nested", dict, [Argument("value", int)])],
            )
            original_cwd = os.getcwd()
            try:
                os.chdir(os.path.dirname(tmpdir))
                html = print_html({"$ref": outer_path}, argument, allow_ref=True)
            finally:
                os.chdir(original_cwd)

        self.assertIn('"value"', html)

    def test_html_escapes_user_content(self) -> None:
        """JSON values, keys, and docs cannot inject executable HTML."""
        from dargs.notebook import print_html

        dangerous_key = '<img src="x" onerror="alert(1)">'
        argument = Argument(
            "root",
            dict,
            [Argument(dangerous_key, str, doc="<script>doc()</script>")],
        )
        rendered = print_html(
            {dangerous_key: "<script>value()</script>"},
            argument,
        )

        self.assertNotIn("<script>", rendered)
        self.assertNotIn("<img ", rendered)
        self.assertIn("&lt;script&gt;value()", rendered)
        self.assertIn("&lt;img src=", rendered)

    def test_html_preserves_only_generated_tooltip_breaks(self) -> None:
        """Generated tooltip breaks remain markup while user tags stay escaped."""
        from dargs.notebook import print_html

        argument = Argument(
            "root",
            dict,
            [Argument("literal<br/>", str)],
        )
        rendered = print_html({"literal<br/>": "value"}, argument)

        self.assertIn("literal&lt;br/&gt;: <br/>", rendered)
        self.assertNotIn("literal<br/>: <br/>", rendered)

    def test_html_validation(self) -> None:
        from dargs.notebook import print_html

        doc_test = "Test doc."
        test_arg = Argument(
            name="test",
            dtype=str,
            doc=doc_test,
            sub_fields=[
                Argument("test_argument", dtype=str, doc=doc_test, default="test"),
            ],
            sub_variants=[
                Variant(
                    "test_variant",
                    doc=doc_test,
                    choices=[
                        Argument(
                            "test_variant_argument",
                            dtype=dict,
                            optional=True,
                            doc=doc_test,
                            sub_fields=[
                                Argument(
                                    "test_repeat",
                                    dtype=list,
                                    repeat=True,
                                    doc=doc_test,
                                    sub_fields=[
                                        Argument(
                                            "test_repeat_item", dtype=bool, doc=doc_test
                                        ),
                                    ],
                                )
                            ],
                        ),
                    ],
                ),
            ],
        )
        jdata = {
            "test_argument": "test1",
            "test_variant": "test_variant_argument",
            "test_repeat": [{"test_repeat_item": False}, {"test_repeat_item": True}],
            "_comment": "This is an example data",
        }
        html = print_html(
            jdata,
            test_arg,
        )
        # https://stackoverflow.com/a/29533744/9567349
        # https://stackoverflow.com/a/35591479/9567349
        magic = """<!DOCTYPE html [
            <!ENTITY nbsp ' '>
            ]>"""
        ET.fromstring(magic + f"<html>{html}</html>")
