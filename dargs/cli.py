from __future__ import annotations

import argparse
import json
import sys

from dargs._version import __version__
from dargs.check import check


def main_parser() -> argparse.ArgumentParser:
    """Create the main parser for the command line interface.

    Returns
    -------
    argparse.ArgumentParser
        The main parser
    """
    parser = argparse.ArgumentParser(
        description="dargs: Argument checking for Python programs"
    )
    subparsers = parser.add_subparsers(help="Sub-commands")
    parser_check = subparsers.add_parser(
        "check", help="Check a JSON file against an Argument"
    )
    parser_check.add_argument(
        "func",
        type=str,
        help="Function that returns an Argument object. E.g., `dargs._test.test_arguments`",
    )
    parser_check.add_argument(
        "jdata",
        type=argparse.FileType("r"),
        default=sys.stdin,
        help="Path to the JSON file. If not given, read from stdin.",
    )
    parser_check.add_argument(
        "--no-strict",
        action="store_false",
        dest="strict",
        help="Do not raise an error if the key is not pre-defined",
    )
    parser_check.set_defaults(entrypoint=check_cli)

    # --version
    parser.add_argument("--version", action="version", version=__version__)
    return parser


def main():
    """Main entry point for the command line interface."""
    parser = main_parser()
    args = parser.parse_args()

    args.entrypoint(**vars(args))


def check_cli(
    *,
    func: str,
    jdata: argparse.FileType,
    strict: bool,
    **kwargs,
) -> None:
    """Normalize and check input data.

    Parameters
    ----------
    func : str
        Function that returns an Argument object. E.g., `dargs._test.test_arguments`
    jdata : argparse.FileType
        File object that contains the JSON data
    strict : bool
        If True, raise an error if the key is not pre-defined

    Returns
    -------
    dict
        normalized data
    """
    module_name, attr_name = func.rsplit(".", 1)
    try:
        mod = __import__(module_name, globals(), locals(), [attr_name])
    except ImportError:
        raise RuntimeError(
            f'Failed to import "{attr_name}" from "{module_name}".\n{sys.exc_info()[1]}'
        )

    if not hasattr(mod, attr_name):
        raise RuntimeError(f'Module "{module_name}" has no attribute "{attr_name}"')
    func = getattr(mod, attr_name)
    arginfo = func()
    data = json.load(jdata)
    return check(arginfo, data, strict=strict)
