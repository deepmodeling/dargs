from context import dargs
import unittest
from dargs import Argument, Variant


class TestNormalizer(unittest.TestCase):

    def test_default(self):
        # naive
        ca = Argument("Key1", int, optional=True, default=1)
        beg = {}
        end = ca.normalize(beg)
        ref = {"Key1": 1}
        self.assertDictEqual(end, ref)
        self.assertDictEqual(beg, {})
        self.assertTrue(end is not beg)
        # inplace
        end1 = ca.normalize(beg, inplace=True)
        self.assertDictEqual(end1, ref)
        self.assertTrue(end1 is beg)
    
    def test_alias(self):
        ca = Argument("Key1", int, alias=["Old1", "Old2"])
        beg = {"Old1": 1}
        end = ca.normalize(beg)
        ref = {"Key1": 1}
        self.assertDictEqual(end, ref)
        self.assertDictEqual(beg, {"Old1": 1})
        self.assertTrue(end is not beg)
        # inplace
        beg1 = {"Old2": 1}
        end1 = ca.normalize(beg1, inplace=True)
        self.assertDictEqual(end1, ref)
        self.assertTrue(end1 is beg1)

    def test_trim(self):
        ca = Argument("Key1", int)
        beg = {"Key1": 1, "_comment": 123}
        end = ca.normalize(beg, trim_pattern="_*")
        ref = {"Key1": 1}
        self.assertDictEqual(end, ref)
        self.assertDictEqual(beg, {"Key1": 1, "_comment": 123})
        self.assertTrue(end is not beg)
        # conflict pattern
        with self.assertRaises(ValueError):
            ca.normalize(beg, trim_pattern="Key1")
        # inplace
        end1 = ca.normalize(beg, inplace=True, trim_pattern="_*")
        self.assertDictEqual(end1, ref)
        self.assertTrue(end1 is beg)

    def test_combined(self):
        ca = Argument("base", dict, [
            Argument("sub1", int, optional=True, default=1, alias=["sub1a"]),
            Argument("sub2", str, optional=True, default="haha", alias=["sub2a"])
        ])
        beg1 = {"base":{}}
        ref1 = {"base":{"sub1":1, "sub2": "haha"}}
        self.assertDictEqual(ca.normalize(beg1), ref1)
        self.assertDictEqual(ca.normalize_value(beg1["base"]), ref1["base"])
        beg2 = {"base":{"sub1a": 2, "sub2a": "hoho", "_comment": None}}
        ref2 = {"base":{"sub1": 2, "sub2": "hoho"}}
        self.assertDictEqual(ca.normalize(beg2, trim_pattern="_*"), ref2)
        self.assertDictEqual(ca.normalize_value(beg2["base"], trim_pattern="_*"), ref2["base"])

    def test_complicated(self):
        ca = Argument("base", dict, [
            Argument("sub1", int, optional=True, default=1, alias=["sub1a"]),
            Argument("sub2", list, [
                Argument("ss1", int, optional=True, default=21, alias=["ss1a"])
            ], repeat=True, alias=["sub2a"])
        ], [
            Variant("vnt_flag", [
                Argument("type1", dict, [
                    Argument("shared", int, optional=True, default=-1, alias=["shareda"]),
                    Argument("vnt1", int, optional=True, default=111, alias=["vnt1a"]),
                ]),
                Argument("type2", dict, [
                    Argument("shared", int, optional=True, default=-2, alias=["sharedb"]),
                    Argument("vnt2", int, optional=True, default=222, alias=["vnt2a"]),
                ], alias = ['type3'])
            ], optional=True, default_tag="type1")
        ])
        beg1 = {"base": {"sub2": [{}, {}]}}
        ref1 = {
            'base': {
                'sub1': 1,
                'sub2': [{'ss1': 21}, {'ss1': 21}], 
                'vnt_flag': "type1",
                'shared': -1, 
                'vnt1': 111}
        }
        self.assertDictEqual(ca.normalize(beg1), ref1)
        self.assertDictEqual(ca.normalize_value(beg1["base"]), ref1["base"])
        beg2 = {
            "base": {
                "sub1a": 2,
                "sub2a": [{"ss1a":22}, {"_comment1": None}],
                "vnt_flag": "type3",
                "sharedb": -3,
                "vnt2a": 223,
                "_comment2": None}
        }
        ref2 = {
            'base': {
                'sub1': 2,
                'sub2': [{'ss1': 22}, {'ss1': 21}], 
                "vnt_flag": "type2",
                'shared': -3, 
                'vnt2': 223}
        }
        self.assertDictEqual(ca.normalize(beg2, trim_pattern="_*"), ref2)
        self.assertDictEqual(ca.normalize_value(beg2["base"], trim_pattern="_*"), ref2["base"])
        with self.assertRaises(ValueError):
            ca.normalize(beg2, trim_pattern="sub*")
        with self.assertRaises(ValueError):
            ca.normalize(beg2, trim_pattern="vnt*")

    def test_dpmd(self):
        import json
        from dpmdargs import normalize, example_json_str
        data = json.loads(example_json_str)
        normalize(data)

if __name__ == "__main__":
    unittest.main()
    
