from __future__ import annotations

import json
import unittest

from jsonschema import validate

from dargs.json_schema import _convert_types, generate_json_schema

from .dpmdargs import example_json_str, gen_args


class TestJsonSchema(unittest.TestCase):
    def test_json_schema(self):
        args = gen_args()
        schema = generate_json_schema(args)
        data = json.loads(example_json_str)
        validate(data, schema)

    def test_convert_types(self):
        self.assertEqual(_convert_types(int), "number")
        self.assertEqual(_convert_types(str), "string")
        self.assertEqual(_convert_types(float), "number")
        self.assertEqual(_convert_types(bool), "boolean")
        self.assertEqual(_convert_types(None), "null")
        self.assertEqual(_convert_types(type(None)), "null")
        self.assertEqual(_convert_types(list), "array")
        self.assertEqual(_convert_types(dict), "object")
        with self.assertRaises(ValueError):
            _convert_types(set)
