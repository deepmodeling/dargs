from __future__ import annotations

import json
import unittest
from typing import List

import dargs
from dargs import Argument, ArgumentEncoder, Variant


class TestDocgen(unittest.TestCase):
    def test_sub_fields(self):
        ca = Argument(
            "base",
            dict,
            [
                Argument("sub1", int, doc="sub doc." * 5),
                Argument(
                    "sub2",
                    [str, dict],
                    [
                        Argument("subsub1", int, doc="subsub doc." * 5),
                        Argument(
                            "subsub2",
                            dict,
                            [Argument("subsubsub1", int, doc="subsubsub doc." * 5)],
                            doc="subsub doc." * 5,
                        ),
                        Argument(
                            "list_of_float",
                            List[float],
                            doc="Check if List[float] works.",
                        ),
                    ],
                    doc="sub doc." * 5,
                ),
            ],
            doc="Base doc. " * 10,
        )
        docstr = ca.gen_doc()
        jsonstr = json.dumps(ca, cls=ArgumentEncoder)
        # print("\n\n"+docstr)

    def test_sub_repeat_list(self):
        ca = Argument(
            "base",
            list,
            [
                Argument("sub1", int, doc="sub doc." * 5),
                Argument(
                    "sub2",
                    [None, str, dict],
                    [
                        Argument("subsub1", int, doc="subsub doc." * 5, optional=True),
                        Argument(
                            "subsub2",
                            list,
                            [Argument("subsubsub1", int, doc="subsubsub doc." * 5)],
                            doc="subsub doc." * 5,
                            repeat=True,
                        ),
                    ],
                    doc="sub doc." * 5,
                ),
            ],
            doc="Base doc. " * 10,
            repeat=True,
        )
        docstr = ca.gen_doc()
        jsonstr = json.dumps(ca, cls=ArgumentEncoder)
        # print("\n\n"+docstr)

    def test_sub_repeat_dict(self):
        ca = Argument(
            "base",
            dict,
            [
                Argument("sub1", int, doc="sub doc." * 5),
                Argument(
                    "sub2",
                    [None, str, dict],
                    [
                        Argument("subsub1", int, doc="subsub doc." * 5, optional=True),
                        Argument(
                            "subsub2",
                            dict,
                            [Argument("subsubsub1", int, doc="subsubsub doc." * 5)],
                            doc="subsub doc." * 5,
                            repeat=True,
                        ),
                    ],
                    doc="sub doc." * 5,
                ),
            ],
            doc="Base doc. " * 10,
            repeat=True,
        )
        docstr = ca.gen_doc()
        jsonstr = json.dumps(ca, cls=ArgumentEncoder)

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
                                Argument(
                                    "vnt1_2",
                                    dict,
                                    [
                                        Argument("vnt1_1_1", int),
                                        Argument("vnt1_1_2", int),
                                    ],
                                ),
                            ],
                            doc="type1 doc here!",
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
                ),
                Variant(
                    "vnt_flag1",
                    [
                        Argument(
                            "type1",
                            dict,
                            [
                                Argument("1shared", int),
                                Argument("1vnt1_1", int),
                                Argument(
                                    "1vnt1_2",
                                    dict,
                                    [
                                        Argument("vnt1_1_1", int),
                                        Argument("vnt1_1_2", int),
                                    ],
                                ),
                            ],
                        ),
                        Argument(
                            "type2",
                            dict,
                            [
                                Argument("1shared", int),
                                Argument("1vnt2_1", int),
                            ],
                        ),
                    ],
                    optional=True,
                    default_tag="type1",
                    doc="another vnt",
                ),
            ],
        )
        docstr = ca.gen_doc(make_anchor=True)
        jsonstr = json.dumps(ca, cls=ArgumentEncoder)
        # print("\n\n"+docstr)

    def test_multi_variants(self):
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
        docstr = ca.gen_doc()
        jsonstr = json.dumps(ca, cls=ArgumentEncoder)
        # print("\n\n"+docstr)

    def test_dpmd(self):
        from .dpmdargs import gen_doc

        dargs.RAW_ANCHOR = False
        docstr = gen_doc(make_anchor=True, make_link=True)
        # print("\n\n"+docstr)
        # with open("out.rst", "w") as of:
        #     print(docstr, file=of)
        # now testing raw anchor
        dargs.RAW_ANCHOR = True
        docstr = gen_doc(make_anchor=True, make_link=True)
        # print("\n\n"+docstr)
        # with open("outr.rst", "w") as of:
        #     print(docstr, file=of)


if __name__ == "__main__":
    unittest.main()
