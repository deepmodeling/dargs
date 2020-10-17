from context import dargs
import unittest
from dargs import Argument, Variant


class TestChecker(unittest.TestCase):

    def test_name_type(self):
        # naive
        ca = Argument("key1", int)
        ca.check({"key1": 10})
        # accept multiple types
        ca = Argument("key1", [int, list, str])
        ca.check({"key1": 10})
        ca.check({"key1": [10, 20]})
        ca.check({"key1": "hello"})
        # possible error
        with self.assertRaises(KeyError):
            ca.check({"key2": 1})
        with self.assertRaises(KeyError):
            ca.check({"key1": 1, "key2": 1}, strict=True)
        with self.assertRaises(TypeError):
            ca.check({"key1": 1.0})
        # special handle of None
        ca = Argument("key1", [int, None])
        ca.check({"key1": None})
        # optional case
        ca = Argument("Key1", int, optional=True)
        ca.check({})

    def test_sub_fields(self):
        ca = Argument("base", dict, [
            Argument("sub1", int),
            Argument("sub2", [str, dict], [
                Argument("subsub1", int),
                Argument("subsub2", dict, [
                    Argument("subsubsub1", int)
                ])
            ])
        ])
        # short one
        test_dict1 = {
            "base": {
                "sub1": 1,
                "sub2": "hello"}}
        self.assertSetEqual(set(ca._get_allowed_sub(test_dict1["base"])),
                            set(test_dict1["base"].keys()))
        ca.check(test_dict1)
        ca.check_value(test_dict1["base"])
        # long one
        test_dict2 = {
            "base": {
                "sub1": 1,
                "sub2": {
                    "subsub1": 11,
                    "subsub2": {
                        "subsubsub1": 111}}}}
        ca.check(test_dict2)
        ca.check_value(test_dict2["base"])
        # expect error
        err_dict1 = {
            "base": {
                "sub1": 1,
                "sub2": {
                    "subsub1": 11,
                    "subsub2": {
                        "subsubsub2": 111}}}} # different name here
        with self.assertRaises(KeyError):
            ca.check(err_dict1)
        err_dict1["base"]["sub2"]["subsub2"]["subsubsub1"] = 111
        ca.check(err_dict1) # now should pass
        with self.assertRaises(KeyError):
            ca.check(err_dict1, strict=True) # but should fail when strict
        err_dict1["base"]["sub2"] = None
        with self.assertRaises(TypeError):
            ca.check(err_dict1)
        
    def test_sub_repeat(self):
        ca = Argument("base", dict, [
            Argument("sub1", int),
            Argument("sub2", str)
        ], repeat=True)
        test_dict1 = {
            "base": [
                {"sub1": 10,
                 "sub2": "hello"},
                {"sub1": 11,
                 "sub2": "world"}
            ]}
        ca.check(test_dict1)
        ca.check_value(test_dict1["base"])
        err_dict1 = {
            "base": [
                {"sub1": 10,
                 "sub2": "hello"},
                {"sub1": 11,
                 "sub3": "world"}
            ]}
        with self.assertRaises(KeyError):
            ca.check(err_dict1)
        err_dict1["base"][1]["sub2"] = "world too"
        ca.check(err_dict1) # now should pass
        with self.assertRaises(KeyError):
            ca.check(err_dict1, strict=True) # but should fail when strict
        err_dict2 = {
            "base": [
                {"sub1": 10,
                 "sub2": "hello"},
                {"sub1": 11,
                 "sub2": None}
            ]}
        with self.assertRaises(TypeError):
            ca.check(err_dict2)

    def test_sub_variants(self):
        ca = Argument("base", dict, [
            Argument("sub1", int),
            Argument("sub2", str)
        ], [
            Variant("vnt_flag", [
                Argument("type1", dict, [
                    Argument("shared", int),
                    Argument("vnt1_1", int),
                    Argument("vnt1_2", dict, [
                        Argument("vnt1_1_1", int)
                    ])
                ]),
                Argument("type2", dict, [
                    Argument("shared", int),
                    Argument("vnt2_1", int),
                ])
            ])
        ])
        test_dict1 = {
            "base": {
                "sub1": 1,
                "sub2": "a",
                "vnt_flag" : "type1",
                "shared": 10,
                "vnt1_1": 11,
                "vnt1_2": {
                    "vnt1_1_1": 111}}}
        self.assertSetEqual(set(ca._get_allowed_sub(test_dict1["base"])),
                            set(test_dict1["base"].keys()))
        ca.check(test_dict1)
        test_dict2 = {
            "base": {
                "sub1": 1,
                "sub2": "a",
                "vnt_flag" : "type2",
                "shared": 20,
                "vnt2_1": 21}}
        self.assertSetEqual(set(ca._get_allowed_sub(test_dict2["base"])),
                            set(test_dict2["base"].keys()))
        ca.check(test_dict2)
        err_dict1 = {
            "base": {
                "sub1": 1,
                "sub2": "a",
                "vnt_flag" : "type2", # here is wrong
                "shared": 10,
                "vnt1_1": 11,
                "vnt1_2": {
                    "vnt1_1_1": 111}}}
        with self.assertRaises(KeyError):
            ca.check(err_dict1)
        err_dict1["base"]["vnt_flag"] = "type1"
        err_dict1["base"]["additional"] = "hahaha"
        ca.check(err_dict1) # now should pass
        with self.assertRaises(KeyError):
            ca.check(err_dict1, strict=True) # but should fail when strict
        err_dict2 = {
            "base": {
                "sub1": 1,
                "sub2": "a",
                "vnt_flag" : "type3", # here is wrong
                "shared": 20,
                "vnt2_1": 21}}
        with self.assertRaises(KeyError):
            ca.check(err_dict2)
        # test optional choice
        test_dict1["base"].pop("vnt_flag")
        with self.assertRaises(KeyError):
            ca.check(test_dict1)
        ca.sub_variants[0].optional = True
        ca.sub_variants[0].default_tag = "type1"
        ca.check(test_dict1)
        # make sure duplicate tag is not allowed
        with self.assertRaises(ValueError):
            Argument("base", dict, [], [
                Variant("flag", [
                    Argument("type1", dict),
                    Argument("type1", dict)])
            ])


if __name__ == "__main__":
    unittest.main()
    
