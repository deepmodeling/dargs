from context import dargs
import unittest
from dargs import Argument, Variant


class TestDocgen(unittest.TestCase):

    def test_sub_fields(self):
        ca = Argument("base", dict, [
            Argument("sub1", int, doc="sub doc." * 5),
            Argument("sub2", [str, dict], [
                Argument("subsub1", int, doc="subsub doc." * 5),
                Argument("subsub2", dict, [
                    Argument("subsubsub1", int, doc="subsubsub doc." * 5)
                ], doc="subsub doc." * 5)
            ], doc="sub doc." * 5)
        ], doc="Base doc. " * 10)
        print("\n")
        print(ca.gen_doc())

    def test_sub_repeat(self):
        ca = Argument("base", dict, [
            Argument("sub1", int, doc="sub doc." * 5),
            Argument("sub2", [None, str, dict], [
                Argument("subsub1", int, doc="subsub doc." * 5, optional=True),
                Argument("subsub2", dict, [
                    Argument("subsubsub1", int, doc="subsubsub doc." * 5)
                ], doc="subsub doc." * 5, repeat=True)
            ], doc="sub doc." * 5)
        ], doc="Base doc. " * 10, repeat=True)
        print("\n")
        print(ca.gen_doc())

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
                        Argument("vnt1_1_1", int),
                        Argument("vnt1_1_2", int)
                    ])
                ], doc="type1 doc here!"),
                Argument("type2", dict, [
                    Argument("shared", int),
                    Argument("vnt2_1", int),
                ])
            ], optional=True, default_tag="type1"),
            Variant("vnt_flag1", [
                Argument("type1", dict, [
                    Argument("1shared", int),
                    Argument("1vnt1_1", int),
                    Argument("1vnt1_2", dict, [
                        Argument("vnt1_1_1", int),
                        Argument("vnt1_1_2", int)
                    ])
                ]),
                Argument("type2", dict, [
                    Argument("1shared", int),
                    Argument("1vnt2_1", int),
                ])
            ], optional=True, default_tag="type1", doc="another vnt")
        ])
        print("\n")
        print(ca.gen_doc())

    def test_dpmd(self):
        from dpmdargs import gen_doc
        print(gen_doc())


if __name__ == "__main__":
    unittest.main()
