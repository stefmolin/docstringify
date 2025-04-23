"""Shared test fixtures."""

from collections import namedtuple
from textwrap import dedent

import pytest

EXAMPLE_MODULE_NAME = 'example_module'
EXAMPLE_FUNCTION_NAME = 'function'

DocstringifyTestCase = namedtuple(
    'DocstringifyTestCase', ('file', 'total_docstrings', 'missing_docstrings')
)


@pytest.fixture
def function_without_args(tmp_path):
    """
    Fixture for generating an example module with a function without args, type
    annotations, or a docstring.
    """
    source_code = dedent(
        f"""
        def {EXAMPLE_FUNCTION_NAME}():
            pass
        """
    )

    tmp_file = tmp_path / f'{EXAMPLE_MODULE_NAME}.py'
    tmp_file.write_text(source_code)

    return DocstringifyTestCase(
        file=tmp_file,
        total_docstrings=2,
        missing_docstrings=[
            EXAMPLE_MODULE_NAME,
            f'{EXAMPLE_MODULE_NAME}.{EXAMPLE_FUNCTION_NAME}',
        ],
    )
