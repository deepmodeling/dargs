from __future__ import annotations

import unittest

from dargs import Argument, Variant


class TestCreation(unittest.TestCase):
    def test_dtype(self):
        ref = Argument("key1", [bool, str, dict])
        ca = Argument("key1", int)
        ca.set_dtype([bool, str, dict])
        self.assertTrue(ca == ref)

    def test_sub_fields(self):
        ref = Argument(
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
        ca = Argument("base", dict)
        s1 = ca.add_subfield("sub1", int)
        s2 = ca.add_subfield("sub2", str)
        ss1 = s2.add_subfield("subsub1", int)
        ss2 = s2.add_subfield("subsub2", dict)
        sss1 = ss2.add_subfield("subsubsub1", int)
        self.assertTrue(ca == ref)
        ref.set_repeat(True)
        ca.set_repeat(True)
        self.assertTrue(ca == ref)

    def test_idx_fields(self):
        s1 = Argument("sub1", int)
        vt1 = Argument(
            "type1",
            dict,
            [
                Argument("shared", str),
                Argument("vnt1_1", dict, [Argument("vnt1_1_1", int)]),
            ],
        )
        vt2 = Argument(
            "type2",
            dict,
            [
                Argument("shared", int),
            ],
        )
        v1 = Variant("vnt_flag", [vt1, vt2])
        ca = Argument("base", dict, [s1], [v1])
        self.assertTrue(ca[""] is ca)
        self.assertTrue(ca["."] is ca)
        self.assertTrue(ca["sub1"] == ca["./sub1"] == s1)
        with self.assertRaises(KeyError):
            ca["sub2"]
        self.assertTrue(ca["[type1]"] is vt1)
        self.assertTrue(ca["[type1]///"] is vt1)
        self.assertTrue(ca["[type1]/vnt1_1/vnt1_1_1"] == Argument("vnt1_1_1", int))
        self.assertTrue(ca["[type2]//shared"] == Argument("shared", int))
        with self.assertRaises(KeyError):
            s1["sub1"]
        self.assertTrue(s1.I["sub1"] is s1)
        self.assertTrue(ca.I["base[type1]"] is vt1)
        self.assertTrue(ca.I["base[type2]//shared"] == Argument("shared", int))

    def test_sub_variants(self):
        ref = Argument(
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
                        ),
                    ],
                )
            ],
        )
        ca = Argument("base", dict)
        s1 = ca.add_subfield("sub1", int)
        s2 = ca.add_subfield("sub2", str)
        v1 = ca.add_subvariant("vnt_flag")
        vt1 = v1.add_choice("type1", dict)
        vt1s0 = vt1.add_subfield("shared", int)
        vt1s1 = vt1.add_subfield("vnt1_1", int)
        vt1s2 = vt1.add_subfield("vnt1_2", dict)
        vt1ss = vt1s2.add_subfield("vnt1_1_1", int)
        vt2 = v1.add_choice("type2")
        vt2s0 = vt2.add_subfield("shared", int)
        vt2s1 = vt2.add_subfield("vnt2_1", int)
        self.assertTrue(ca == ref)
        # make sure we can modify the reference
        ref1 = Argument(
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
                        ),
                    ],
                    optional=True,
                    default_tag="type1",
                )
            ],
        )
        v1.set_default("type1")
        self.assertTrue(ca == ref1)
        v1.set_default(False)
        self.assertTrue(ca == ref)

    def test_idx_variants(self):
        vt1 = Argument(
            "type1",
            dict,
            [
                Argument("shared", int),
                Argument("vnt1_1", int),
                Argument("vnt1_2", dict, [Argument("vnt1_1_1", int)]),
            ],
        )
        vt2 = Argument(
            "type2",
            dict,
            [
                Argument("shared", int),
                Argument("vnt2_1", int),
            ],
        )
        vnt = Variant("vnt_flag", [vt1, vt2])
        self.assertTrue(vnt["type1"] is vt1)
        self.assertTrue(vnt["type2"] is vt2)
        with self.assertRaises(KeyError):
            vnt["type3"]

    def test_complicated(self):
        ref = Argument(
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
        ca = Argument("base", dict)
        s1 = ca.add_subfield("sub1", int)
        s2 = ca.add_subfield("sub2", str)
        v1 = ca.add_subvariant("vnt_flag")
        vt1 = v1.add_choice("type1", dict)
        vt1s0 = vt1.add_subfield("shared", int)
        vt1s1 = vt1.add_subfield("vnt1_1", int)
        vt1s2 = vt1.add_subfield("vnt1_2", dict)
        vt1ss = vt1s2.add_subfield("vnt1_1_1", int)
        vt2 = v1.add_choice("type2")
        vt2s0 = vt2.add_subfield("shared", int)
        vt2s1 = vt2.add_subfield("vnt2_1", int)
        vt3 = v1.add_choice("type3")
        vt3s1 = vt3.add_subfield("vnt3_1", int)
        vt3f1 = vt3.add_subvariant("vnt3_flag1")
        vt3f1t1 = vt3f1.add_choice("v3f1t1")
        vt3f1t1s1 = vt3f1t1.add_subfield("v3f1t1_1", int)
        vt3f1t1s2 = vt3f1t1.add_subfield("v3f1t1_2", int)
        vt3f1t2 = vt3f1.add_choice("v3f1t2")
        vt3f1t2s1 = vt3f1t2.add_subfield("v3f1t2_1", int)
        vt3f2 = vt3.add_subvariant("vnt3_flag2")
        vt3f2t1 = vt3f2.add_choice("v3f2t1")
        vt3f2t1s1 = vt3f2t1.add_subfield("v3f2t1_1", int)
        vt3f2t1s2 = vt3f2t1.add_subfield("v3f2t1_2", int)
        vt3f2t2 = vt3f2.add_choice("v3f2t2")
        vt3f2t2s1 = vt3f2t2.add_subfield("v3f2t2_1", int)
        self.assertTrue(ca == ref)
        self.assertTrue(ca["[type3][vnt3_flag1=v3f1t1]"] is vt3f1t1)
        self.assertTrue(ca.I["base[type3][vnt3_flag1=v3f1t1]/v3f1t1_2"] is vt3f1t1s2)
        self.assertTrue(ca.I["base[type3][vnt3_flag1=v3f1t2]/v3f1t2_1"] is vt3f1t2s1)
        self.assertTrue(ca.I["base[type3][vnt3_flag2=v3f2t1]/v3f2t1_1"] is vt3f2t1s1)
        self.assertTrue(ca.I["base[type3][vnt3_flag2=v3f2t2]/v3f2t2_1"] is vt3f2t2s1)
        with self.assertRaises((KeyError, ValueError)):
            ca.I["base[type3][v3f2t2]"]
        with self.assertRaises((KeyError, ValueError)):
            ca.I["base[type3][vnt3_flag3=v3f2t2]/v3f2t2_1"]


if __name__ == "__main__":
    unittest.main()
