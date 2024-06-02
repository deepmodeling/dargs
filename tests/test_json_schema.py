import json
import unittest
from .dpmdargs import gen_args, example_json_str

from dargs.json_schema import generate_json_schema
from jsonschema import validate


class TestJsonSchema(unittest.TestCase):
    def test_json_schema(self):
        args = gen_args()
        schema = generate_json_schema(args)
        data = json.loads(example_json_str)
        validate(data, schema)
