from __future__ import annotations

import argparse
import json
import sys
from typing import IO

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
        "check",
        help="Check a JSON file against an Argument",
        epilog="Example: dargs check -f dargs._test.test_arguments test_arguments.json",
    )
    parser_check.add_argument(
        "-f",
        "--func",
        type=str,
        help="Function that returns an Argument object. E.g., `dargs._test.test_arguments`",
        required=True,
    )
    parser_check.add_argument(
        "jdata",
        type=argparse.FileType("r"),
        default=[sys.stdin],
        nargs="*",
        help="Path to the JSON file. If not given, read from stdin.",
    )
    parser_check.add_argument(
        "--no-strict",
        action="store_false",
        dest="strict",
        help="Do not raise an error if the key is not pre-defined",
    )
    parser_check.add_argument(
        "--trim-pattern",
        type=str,
        default="_*",
        help="Pattern to trim the key",
    )
    parser_check.set_defaults(entrypoint=check_cli)

    # doc subcommand
    parser_doc = subparsers.add_parser(
        "doc",
        help="Print documentation for an Argument",
        epilog="Example: dargs doc -f dargs._test.test_arguments [arg_path]",
    )
    parser_doc.add_argument(
        "-f",
        "--func",
        type=str,
        help="Function that returns an Argument or list of Arguments. E.g., `dargs._test.test_arguments`",
        required=True,
    )
    parser_doc.add_argument(
        "arg",
        type=str,
        nargs="?",
        default=None,
        help="Optional argument path (e.g., 'base/sub1'). If not provided, prints all top-level arguments.",
    )
    parser_doc.set_defaults(entrypoint=doc_cli)

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
    jdata: list[IO],
    strict: bool,
    **kwargs,
) -> None:
    """Normalize and check input data.

    Parameters
    ----------
    func : str
        Function that returns an Argument object. E.g., `dargs._test.test_arguments`
    jdata : IO
        File object that contains the JSON data
    strict : bool
        If True, raise an error if the key is not pre-defined

    Returns
    -------
    dict
        normalized data
    """
    module_name, attr_name = func.strip().rsplit(".", 1)
    try:
        mod = __import__(module_name, globals(), locals(), [attr_name])
    except ImportError as e:
        raise RuntimeError(
            f'Failed to import "{attr_name}" from "{module_name}".\n{sys.exc_info()[1]}'
        ) from e

    if not hasattr(mod, attr_name):
        raise RuntimeError(f'Module "{module_name}" has no attribute "{attr_name}"')
    func_obj = getattr(mod, attr_name)
    arginfo = func_obj()
    for jj in jdata:
        data = json.load(jj)
        check(arginfo, data, strict=strict)


def doc_cli(
    *,
    func: str,
    arg: str | None = None,
    **kwargs,
) -> None:
    """Print documentation for an Argument.

    Parameters
    ----------
    func : str
        Function that returns an Argument or list of Arguments. E.g., `dargs._test.test_arguments`
    arg : str, optional
        Optional argument path (e.g., 'base/sub1'). If not provided, prints all top-level arguments.
    """
    try:
        module_name, attr_name = func.strip().rsplit(".", 1)
    except ValueError as e:
        raise RuntimeError(
            f'Function must be in format "module.function", got: "{func}"'
        ) from e
    try:
        mod = __import__(module_name, globals(), locals(), [attr_name])
    except ImportError as e:
        raise RuntimeError(
            f'Failed to import "{attr_name}" from "{module_name}".\n{sys.exc_info()[1]}'
        ) from e

    if not hasattr(mod, attr_name):
        raise RuntimeError(f'Module "{module_name}" has no attribute "{attr_name}"')
    func_obj = getattr(mod, attr_name)
    arginfo = func_obj()

    # Handle both single Argument and list of Arguments
    if isinstance(arginfo, list):
        args_list = arginfo
    else:
        args_list = [arginfo]

    # If no specific arg path is provided, print all top-level arguments
    if arg is None:
        for argument in args_list:
            print(argument.gen_doc())
            print()  # Add blank line between arguments
    else:
        # Navigate to the specific argument by path
        path_parts = arg.split("/")
        found = False

        # First, try to find the argument in the top-level list
        for argument in args_list:
            if argument.name == path_parts[0]:
                # Found the top-level argument
                current_arg = argument
                # Navigate through sub-fields if path has more parts
                for part in path_parts[1:]:
                    if part in current_arg.sub_fields:
                        current_arg = current_arg.sub_fields[part]
                    else:
                        raise RuntimeError(
                            f'Argument path "{arg}" not found: "{part}" is not a sub-field of "{current_arg.name}"'
                        )
                print(current_arg.gen_doc())
                found = True
                break

        if not found:
            raise RuntimeError(
                f'Argument path "{arg}" not found: no top-level argument named "{path_parts[0]}"'
            )
