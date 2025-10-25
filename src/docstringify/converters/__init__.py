"""Docstring converters."""

from .base import DocstringConverter
from .google import GoogleDocstringConverter
from .numpydoc import NumpydocDocstringConverter
from .stub import StubDocstringConverter

CONVERTERS: dict[
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

__all__ = [
    'CONVERTERS',
    'DocstringConverter',
    'GoogleDocstringConverter',
    'NumpydocDocstringConverter',
    'StubDocstringConverter',
]
