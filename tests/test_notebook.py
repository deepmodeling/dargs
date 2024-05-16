from __future__ import annotations

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
    def test_html_validation(self):
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
