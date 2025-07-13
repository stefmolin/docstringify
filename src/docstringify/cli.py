"""CLI for Docstringify."""

from __future__ import annotations

import argparse
import sys
from enum import StrEnum, auto
from functools import partial
from typing import TYPE_CHECKING

from . import __doc__ as pkg_description
from . import __version__
from .converters import (
    GoogleDocstringConverter,
    NumpydocDocstringConverter,
    StubDocstringConverter,
)
from .traversal import DocstringTransformer, DocstringVisitor

if TYPE_CHECKING:
    from collections.abc import Sequence


PROG = __package__
"""CLI name."""

STYLES: dict[
    str,
    type[GoogleDocstringConverter]
    | type[NumpydocDocstringConverter]
    | type[StubDocstringConverter],
] = {
    'google': GoogleDocstringConverter,
    'numpydoc': NumpydocDocstringConverter,
    'stub': StubDocstringConverter,
}
"""Mapping of docstring style name to the converter class (:mod:`.converters`)."""

CLI_DEFAULTS = {'threshold': 1.0}
"""CLI default values."""


class DocstringifyRunModes(StrEnum):
    """Run modes for Docstringify's CLI."""

    CHECK = auto()
    """Docstringify mode that checks for missing docstrings only."""

    EDIT = auto()
    """Docstringify mode that injects templates for missing docstrings into the
    source code."""

    SUGGEST = auto()
    """Docstringify mode that suggests templates for missing docstrings without
    editing the source code."""


def _process_files(
    mode: DocstringifyRunModes, args: argparse.Namespace
) -> tuple[int, int]:
    """
    Process the filenames passed in as command line arguments.

    Parameters
    ----------
    mode : DocstringifyRunModes
        The mode in which to run Docstringify.
    args : argparse.Namespace
        The command line arguments.

    Returns
    -------
    tuple[int, int]
        A tuple containing the number of missing docstrings and the total number of
        docstrings expected.
    """
    get_docstring_processor = (
        partial(
            DocstringTransformer,
            converter=STYLES[args.style],
            overwrite=bool(args.overwrite),
            verbose=args.verbose,
        )
        if mode == DocstringifyRunModes.EDIT
        else partial(
            DocstringVisitor,
            converter=None
            if mode == DocstringifyRunModes.CHECK
            else STYLES[args.style],
            verbose=args.verbose,
        )
    )

    docstrings_expected = missing_docstrings = 0
    for file in args.filenames:
        processor = get_docstring_processor(file)
        processor.process_file()
        missing_docstrings += len(processor.missing_docstrings)
        docstrings_expected += processor.docstrings_inspected

    return missing_docstrings, docstrings_expected


def _run(mode: DocstringifyRunModes, args: argparse.Namespace) -> int:
    """
    Run Docstringify in the specified mode with the provided command line arguments.

    Parameters
    ----------
    mode : DocstringifyRunModes
        The run mode.
    args : argparse.Namespace
        The command line arguments.

    Returns
    -------
    int
        Exit code for the process, where non-zero values indicate errors.
    """
    missing_docstrings, docstrings_expected = _process_files(mode, args)

    if mode == DocstringifyRunModes.CHECK:
        if (
            docstrings_expected
            and (missing_percentage := (missing_docstrings / docstrings_expected))
            > 1 - args.threshold
        ):
            print(f'Missing {missing_percentage:.0%} of docstrings', file=sys.stderr)
            print(
                f'Your settings require {args.threshold:.0%} of docstrings to be present',
                file=sys.stderr,
            )
            return 1
        return 0

    # modes suggest and edit behave the same
    if docstrings_expected and missing_docstrings:
        return 1
    return 0


def _populate_subparser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    subcommand: DocstringifyRunModes,
    help_msg: str,
) -> argparse.ArgumentParser:
    """
    Populate an argument subparser for handling subcommands from the main CLI.

    Parameters
    ----------
    subparsers : argparse._SubParsersAction[argparse.ArgumentParser]
        The result of calling the :meth:`argparse.ArgumentParser.add_subparsers` method
        on the main argument parser.
    subcommand : DocstringifyRunModes
        The run mode for which to populate the parser.
    help_msg : str
        The help message to include for the subcommand.

    Returns
    -------
    argparse.ArgumentParser
        The populated subparser.
    """
    parser = subparsers.add_parser(subcommand, help=help_msg)

    parser.add_argument(
        'filenames', nargs='+', metavar='filename', help='filename(s) to process'
    )

    if subcommand == DocstringifyRunModes.CHECK:
        parser.add_argument(
            '--threshold',
            type=float,
            default=CLI_DEFAULTS['threshold'],
            help='the percentage of docstrings that must be present to pass',
        )
    else:
        if subcommand == DocstringifyRunModes.EDIT:
            parser.add_argument(
                '--overwrite',
                action='store_true',
                help='whether to overwrite the existing file with the changes',
            )
        parser.add_argument(
            '--style',
            choices=STYLES.keys(),
            required=True,
            help='docstring style to use',
        )

    parser.add_argument('--verbose', action='store_true', help='run in verbose mode')
    parser.set_defaults(run=partial(_run, subcommand))

    return parser


def _create_parser() -> argparse.ArgumentParser:
    """
    Create an argument parser for the CLI.

    Returns
    -------
    argparse.ArgumentParser
        The argument parser for the CLI.
    """
    parser = argparse.ArgumentParser(prog=PROG, description=pkg_description)
    parser.add_argument(
        '--version', action='version', version=f'%(prog)s {__version__}'
    )

    subparsers = parser.add_subparsers(title='modes')
    for mode, help_msg in [
        (
            DocstringifyRunModes.CHECK,
            'use Docstringify to check whether files have the required docstrings',
        ),
        (
            DocstringifyRunModes.EDIT,
            'use Docstringify to edit files to inject docstring templates for you',
        ),
        (
            DocstringifyRunModes.SUGGEST,
            'use Docstringify to review files and suggest templates for missing docstrings',
        ),
    ]:
        _populate_subparser(subparsers, mode, help_msg)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """
    Flag missing docstrings and, optionally, generate them from signatures and
    type annotations.

    Parameters
    ----------
    argv : Sequence[str] | None, default=None
        The arguments passed on the command line.

    Returns
    -------
    int
        Exit code for the process, where non-zero values indicate errors.
    """
    parser = _create_parser()
    args = parser.parse_args(argv)
    return args.run(args)


if __name__ == '__main__':
    raise SystemExit(main())
