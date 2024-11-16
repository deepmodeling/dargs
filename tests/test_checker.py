from __future__ import annotations

import unittest
from typing import List

from dargs import Argument, Variant
from dargs.dargs import ArgumentKeyError, ArgumentTypeError, ArgumentValueError


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
        with self.assertRaises(ArgumentKeyError):
            ca.check({"key2": 1})
        with self.assertRaises(ArgumentKeyError):
            ca.check({"key1": 1, "key2": 1}, strict=True)
        with self.assertRaises(ArgumentTypeError):
            ca.check({"key1": 1.0})
        # special handle of None
        ca = Argument("key1", [int, None])
        ca.check({"key1": None})
        # special handel of int and float
        ca = Argument("key1", float)
        ca.check({"key1": 1})
        # list[int]
        ca = Argument("key1", List[float])
        ca.check({"key1": [1, 2.0, 3]})
        with self.assertRaises(ArgumentTypeError):
            ca.check({"key1": [1, 2.0, "3"]})
        ca = Argument("key1", List[float], default=[], optional=True)
        with self.assertRaises(ArgumentTypeError):
            ca.check({"key1": [1, 2.0, "3"]})
        # optional case
        ca = Argument("key1", int, optional=True)
        ca.check({})
        # extra checker
        ca = Argument("key1", int, extra_check=lambda v: v > 0)
        ca.check({"key1": 1})
        with self.assertRaises(ArgumentValueError):
            ca.check({"key1": 0})
        # check any keywords
        ca = Argument("kwargs", dict)
        anydict = {"this": 1, "that": 2, "any": 3}
        ca.check({"kwargs": anydict}, strict=True)
        ca.check_value(anydict)

    def test_sub_fields(self):
        ca = Argument(
            "base",
            dict,
            [
                Argument("sub1", int),
                Argument(
                    "sub2",
                    [str, dict],
                    [
                        Argument("subsub1", int),
                        Argument("subsub2", dict, [Argument("subsubsub1", int)]),
                    ],
                ),
            ],
        )
        # short one
        test_dict1 = {"base": {"sub1": 1, "sub2": "hello"}}
        self.assertSetEqual(
            set(ca.flatten_sub(test_dict1["base"]).keys()),
            set(test_dict1["base"].keys()),
        )
        ca.check(test_dict1)
        ca.check_value(test_dict1["base"])
        # long one
        test_dict2 = {
            "base": {"sub1": 1, "sub2": {"subsub1": 11, "subsub2": {"subsubsub1": 111}}}
        }
        ca.check(test_dict2)
        ca.check_value(test_dict2["base"])
        # expect error
        err_dict1 = {
            "base": {"sub1": 1, "sub2": {"subsub1": 11, "subsub2": {"subsubsub2": 111}}}
        }  # different name here
        with self.assertRaises(ArgumentKeyError):
            ca.check(err_dict1)
        err_dict1["base"]["sub2"]["subsub2"]["subsubsub1"] = 111
        ca.check(err_dict1)  # now should pass
        with self.assertRaises(ArgumentKeyError) as cm:
            ca.check(err_dict1, strict=True)  # but should fail when strict
        self.assertIn("Did you mean: subsubsub1?", str(cm.exception))
        err_dict1["base"]["sub2"] = None
        with self.assertRaises(ArgumentTypeError):
            ca.check(err_dict1)
        # make sure no dup keys is allowed
        with self.assertRaises(ValueError):
            Argument("base", dict, [Argument("sub1", int), Argument("sub1", int)])

    def test_sub_repeat_list(self):
        ca = Argument(
            "base", list, [Argument("sub1", int), Argument("sub2", str)], repeat=True
        )
        test_dict1 = {
            "base": [{"sub1": 10, "sub2": "hello"}, {"sub1": 11, "sub2": "world"}]
        }
        ca.check(test_dict1)
        ca.check_value(test_dict1["base"])
        err_dict1 = {
            "base": [{"sub1": 10, "sub2": "hello"}, {"sub1": 11, "sub3": "world"}]
        }
        with self.assertRaises(ArgumentKeyError):
            ca.check(err_dict1)
        err_dict1["base"][1]["sub2"] = "world too"
        ca.check(err_dict1)  # now should pass
        with self.assertRaises(ArgumentKeyError):
            ca.check(err_dict1, strict=True)  # but should fail when strict
        err_dict2 = {
            "base": [{"sub1": 10, "sub2": "hello"}, {"sub1": 11, "sub2": None}]
        }
        with self.assertRaises(ArgumentTypeError):
            ca.check(err_dict2)

    def test_sub_repeat_dict(self):
        ca = Argument(
            "base", dict, [Argument("sub1", int), Argument("sub2", str)], repeat=True
        )
        test_dict1 = {
            "base": {
                "item1": {"sub1": 10, "sub2": "hello"},
                "item2": {"sub1": 11, "sub2": "world"},
            }
        }
        ca.check(test_dict1)
        ca.check_value(test_dict1["base"])
        err_dict1 = {
            "base": {
                "item1": {"sub1": 10, "sub2": "hello"},
                "item2": {"sub1": 11, "sub3": "world"},
            }
        }
        with self.assertRaises(ArgumentKeyError):
            ca.check(err_dict1)
        err_dict1["base"]["item2"]["sub2"] = "world too"
        ca.check(err_dict1)  # now should pass
        with self.assertRaises(ArgumentKeyError):
            ca.check(err_dict1, strict=True)  # but should fail when strict
        err_dict2 = {
            "base": {
                "item1": {"sub1": 10, "sub2": "hello"},
                "item2": {"sub1": 11, "sub2": None},
            }
        }
        with self.assertRaises(ArgumentTypeError):
            ca.check(err_dict2)
        err_dict3 = {
            "base": {
                "item1": {"sub1": 10, "sub2": "hello"},
                "item2": "not_a_dict_error",
            }
        }
        with self.assertRaises(ArgumentTypeError):
            ca.check(err_dict3)

    def test_sub_variants(self):
        ca = Argument(
            "base",
            dict,
            [Argument("sub1", int), Argument("sub2", str)],
            [
                Variant(
                    "vnt_flag",
                    [
                        Argument(
                            "type1",
                            dict,
                            [
                                Argument("shared", int),
                                Argument("vnt1_1", int),
                                Argument("vnt1_2", dict, [Argument("vnt1_1_1", int)]),
                            ],
                        ),
                        Argument(
                            "type2",
                            dict,
                            [
                                Argument("shared", int),
                                Argument("vnt2_1", int),
                            ],
                            alias=["type2a"],
                        ),
                        Argument(
                            "type3",
                            dict,
                            [Argument("vnt3_1", int)],
                            [  # testing cascade variants here
                                Variant(
                                    "vnt3_flag1",
                                    [
                                        Argument(
                                            "v3f1t1",
                                            dict,
                                            [
                                                Argument("v3f1t1_1", int),
                                                Argument("v3f1t1_2", int),
                                            ],
                                        ),
                                        Argument(
                                            "v3f1t2", dict, [Argument("v3f1t2_1", int)]
                                        ),
                                    ],
                                ),
                                Variant(
                                    "vnt3_flag2",
                                    [
                                        Argument(
                                            "v3f2t1",
                                            dict,
                                            [
                                                Argument("v3f2t1_1", int),
                                                Argument("v3f2t1_2", int),
                                            ],
                                        ),
                                        Argument(
                                            "v3f2t2", dict, [Argument("v3f2t2_1", int)]
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                )
            ],
        )
        test_dict1 = {
            "base": {
                "sub1": 1,
                "sub2": "a",
                "vnt_flag": "type1",
                "shared": 10,
                "vnt1_1": 11,
                "vnt1_2": {"vnt1_1_1": 111},
            }
        }
        self.assertSetEqual(
            set(ca.flatten_sub(test_dict1["base"]).keys()),
            set(test_dict1["base"].keys()),
        )
        ca.check(test_dict1)
        test_dict2 = {
            "base": {
                "sub1": 1,
                "sub2": "a",
                "vnt_flag": "type2",
                "shared": 20,
                "vnt2_1": 21,
            }
        }
        self.assertSetEqual(
            set(ca.flatten_sub(test_dict2["base"]).keys()),
            set(test_dict2["base"].keys()),
        )
        ca.check(test_dict2, strict=True)
        test_dict2["base"]["vnt_flag"] = "type2a"
        ca.check(test_dict2, strict=True)
        err_dict1 = {
            "base": {
                "sub1": 1,
                "sub2": "a",
                "vnt_flag": "type2",  # here is wrong
                "shared": 10,
                "vnt1_1": 11,
                "vnt1_2": {"vnt1_1_1": 111},
            }
        }
        with self.assertRaises(ArgumentKeyError):
            ca.check(err_dict1)
        err_dict1["base"]["vnt_flag"] = "type1"
        ca.check(err_dict1, strict=True)  # no additional should pass
        err_dict1["base"]["additional"] = "hahaha"
        ca.check(err_dict1)  # without strict should pass
        with self.assertRaises(ArgumentKeyError):
            ca.check(err_dict1, strict=True)  # but should fail when strict
        err_dict2 = {
            "base": {
                "sub1": 1,
                "sub2": "a",
                "vnt_flag": "badtype",  # here is wrong
                "shared": 20,
                "vnt2_1": 21,
            }
        }
        with self.assertRaises(ArgumentValueError) as cm:
            ca.check(err_dict2)
        self.assertIn("Did you mean: type3?", str(cm.exception))
        # test optional choice
        test_dict1["base"].pop("vnt_flag")
        with self.assertRaises(ArgumentKeyError):
            ca.check(test_dict1)
        ca.sub_variants["vnt_flag"].optional = True
        ca.sub_variants["vnt_flag"].default_tag = "type1"
        ca.check(test_dict1)
        # test cascade variants
        test_dict3 = {
            "base": {
                "sub1": 1,
                "sub2": "a",
                "vnt_flag": "type3",
                "vnt3_1": 31,
                "vnt3_flag1": "v3f1t1",
                "vnt3_flag2": "v3f2t2",
                "v3f1t1_1": 3111,
                "v3f1t1_2": 3112,
                "v3f2t2_1": 3221,
            }
        }
        self.assertSetEqual(
            set(ca.flatten_sub(test_dict3["base"]).keys()),
            set(test_dict3["base"].keys()),
        )
        ca.check(test_dict3, strict=True)
        test_dict3["base"].pop("vnt3_flag2")
        with self.assertRaises(ArgumentKeyError):
            ca.check(test_dict3)
        ca.sub_variants["vnt_flag"].choice_dict["type3"].sub_variants[
            "vnt3_flag2"
        ].optional = True
        ca.sub_variants["vnt_flag"].choice_dict["type3"].sub_variants[
            "vnt3_flag2"
        ].default_tag = "v3f2t2"
        ca.check(test_dict3, strict=True)
        # make sure duplicate tag is not allowed
        with self.assertRaises(ValueError):
            Argument(
                "base",
                dict,
                [],
                [Variant("flag", [Argument("type1", dict), Argument("type1", dict)])],
            )
        with self.assertRaises(ValueError):
            Argument(
                "base",
                dict,
                [],
                [
                    Variant("flag", [Argument("type1", dict)]),
                    Variant("flag", [Argument("type2", dict)]),
                ],
            )


if __name__ == "__main__":
    unittest.main()
