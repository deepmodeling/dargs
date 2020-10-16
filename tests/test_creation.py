from context import dargs
import unittest
from dargs import Argument, Variant


class TestCreation(unittest.TestCase):

    def test_dtype(self):
        ref = Argument("key1", [bool, str, dict])
        ca = Argument("key1", int)
        ca.set_dtype([bool, str, dict])
        self.assertTrue(ca == ref)

    def test_sub_fields(self):
        ref = Argument("base", dict, [
            Argument("sub1", int),
            Argument("sub2", [str, dict], [
                Argument("subsub1", int),
                Argument("subsub2", dict, [
                    Argument("subsubsub1", int)
                ])
            ])
        ])
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

    def test_sub_variants(self):
        ref = Argument("base", dict, [
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
        
        ref1 = Argument("base", dict, [
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
            ], optional=True, default_tag="type1")
        ])
        v1.set_default("type1")
        self.assertTrue(ca == ref1)
        v1.set_default(False)
        self.assertTrue(ca == ref)


if __name__ == "__main__":
    unittest.main()
