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
        print(ca.gen_doc())

    def test_sub_repeat(self):
        ca = Argument("base", dict, [
            Argument("sub1", int, doc="sub doc." * 5),
            Argument("sub2", [str, dict], [
                Argument("subsub1", int, doc="subsub doc." * 5, optional=True),
                Argument("subsub2", dict, [
                    Argument("subsubsub1", int, doc="subsubsub doc." * 5)
                ], doc="subsub doc." * 5, repeat=True)
            ], doc="sub doc." * 5)
        ], doc="Base doc. " * 10, repeat=True)
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
                        Argument("vnt1_1_1", int)
                    ])
                ]),
                Argument("type2", dict, [
                    Argument("shared", int),
                    Argument("vnt2_1", int),
                ])
            ], optional=True, default_tag="type1")
        ], doc="very long doc. " * 20)
        print(ca.gen_doc())


if __name__ == "__main__":
    unittest.main()
