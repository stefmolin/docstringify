"""Docstring components."""

from __future__ import annotations

from typing import Final, NamedTuple

NO_DEFAULT: Final = object()
DESCRIPTION_PLACEHOLDER = '__description__'
PARAMETER_TYPE_PLACEHOLDER = '__type__'
RETURN_TYPE_PLACEHOLDER = '__return_type__'


class Parameter(NamedTuple):
    """__description__"""

    name: str
    type_: str
    category: str | None
    default: str | NO_DEFAULT


class Function(NamedTuple):
    """__description__"""

    parameters: tuple[Parameter, ...]
    return_type: str | None
