"""Docstring converters."""

from .base import DocstringConverter
from .google import GoogleDocstringConverter
from .numpydoc import NumpydocDocstringConverter
from .stub import StubDocstringConverter

CONVERTER_LOOKUP: dict[
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
    'CONVERTER_LOOKUP',
    'DocstringConverter',
    'GoogleDocstringConverter',
    'NumpydocDocstringConverter',
    'StubDocstringConverter',
]
