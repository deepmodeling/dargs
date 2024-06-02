from __future__ import annotations

import json
import unittest

from jsonschema import validate

from dargs.json_schema import generate_json_schema

from .dpmdargs import example_json_str, gen_args


class TestJsonSchema(unittest.TestCase):
    def test_json_schema(self):
        args = gen_args()
        schema = generate_json_schema(args)
        data = json.loads(example_json_str)
        validate(data, schema)
