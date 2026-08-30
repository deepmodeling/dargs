from __future__ import annotations

from typing import List

from dargs.dargs import Argument


def test_arguments() -> list[Argument]:
    """Returns a list of arguments.

    Returns
    -------
    list[Argument]
        A list of test arguments
    """
    return [
        Argument(name="test1", dtype=int, doc="Argument 1"),
        Argument(name="test2", dtype=[float, None], doc="Argument 2"),
        Argument(
            name="test3",
            dtype=List[str],
            default=["test"],
            optional=True,
            doc="Argument 3",
        ),
        Argument(
            "base",
            dict,
            [
                Argument("sub1", int, doc="Sub argument 1"),
                Argument(
                    "sub2",
                    dict,
                    [
                        Argument("subsub1", int, doc="Sub-sub argument 1"),
                    ],
                    doc="Sub argument 2",
                ),
            ],
            optional=True,
            doc="Base argument with nested structure",
        ),
    ]


__all__ = [
    "test_arguments",
]
