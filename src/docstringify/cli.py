"""CLI for Docstringify."""

from __future__ import annotations

import argparse
import sys
from functools import partial
from typing import Sequence

from . import __doc__ as pkg_description
from . import __version__
from .converters import GoogleDocstringConverter, NumpydocDocstringConverter
from .traversal import DocstringTransformer, DocstringVisitor

PROG = __package__
STYLES = {'google': GoogleDocstringConverter, 'numpydoc': NumpydocDocstringConverter}
CLI_DEFAULTS = {'threshold': 1.0}


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
        Exit code for the process, where non-zero values indicate errors, and ``1``
        indicates that more than the allowed percentage of docstrings were missing.
    """

    parser = argparse.ArgumentParser(prog=PROG, description=pkg_description)
    parser.add_argument('filenames', nargs='*', help='Filenames to process')
    parser.add_argument(
        '--version', action='version', version=f'%(prog)s {__version__}'
    )

    run_group = parser.add_argument_group('Run options')
    handle_missing_docstring = run_group.add_mutually_exclusive_group(required=False)
    handle_missing_docstring.add_argument(
        '--make-changes',
        choices=STYLES.keys(),
        help='Whether to insert docstring templates for items missing docstrings',
    )
    handle_missing_docstring.add_argument(
        '--make-changes-inplace',
        choices=STYLES.keys(),
        help=(
            'Whether to insert docstring templates for items missing docstrings, '
            'overwriting the original file'
        ),
    )
    handle_missing_docstring.add_argument(
        '--suggest-changes',
        choices=STYLES.keys(),
        help='Whether to print out docstring templates for items missing docstrings',
    )
    run_group.add_argument(
        '--threshold',
        type=float,
        default=CLI_DEFAULTS['threshold'],
        help='The percentage of docstrings that must be present to pass',
    )
    args = parser.parse_args(argv)

    if style := (
        args.make_changes or args.make_changes_inplace or args.suggest_changes
    ):
        converter = STYLES[style]
    else:
        converter = None

    get_docstring_processor = (
        partial(
            DocstringTransformer,
            converter=converter,
            **{'overwrite': bool(args.make_changes_inplace)},
        )
        if args.make_changes or args.make_changes_inplace
        else partial(DocstringVisitor, converter=converter)
    )

    docstrings_processed = missing_docstrings = 0
    for file in args.filenames:
        processor = get_docstring_processor(file)
        processor.process_file()
        missing_docstrings += len(processor.missing_docstrings)
        docstrings_processed += processor.docstrings_inspected

    if (
        docstrings_processed
        and (missing_percentage := (missing_docstrings / docstrings_processed))
        > 1 - args.threshold
    ):
        print(f'Missing {missing_percentage:.0%} of docstrings', file=sys.stderr)
        print(
            f'Your settings require {args.threshold:.0%} of docstrings to be present',
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
