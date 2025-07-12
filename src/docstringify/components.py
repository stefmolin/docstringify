"""Docstring components."""

from __future__ import annotations

from typing import Final, NamedTuple

NO_DEFAULT: Final = object()
"""Sentinel value indicating that there is no default value. This is necessary because
``None`` has a different meaning in certain contexts of the AST traversal."""

DESCRIPTION_PLACEHOLDER: Final[str] = '__description__'
"""Docstring placeholder for description fields."""

PARAMETER_TYPE_PLACEHOLDER: Final[str] = '__type__'
"""Docstring placeholder for the parameter type, when Docstringify can't determine it."""

RETURN_TYPE_PLACEHOLDER: Final[str] = '__return_type__'
"""Docstring placeholder for the return type, when Docstringify can't determine it."""


class Parameter(NamedTuple):
    """Information about an individual parameter to a function."""

    name: str
    """The name of the parameter."""

    type_: str
    """The parameter's data type."""

    category: str | None
    """The parameter's category, if there is one. This is used to pass additional
    information, for example, to indicate that an argument is positional-only."""

    default: str | NO_DEFAULT
    """A string specifying the default value, if there is one, otherwise,
    :const:`.NO_DEFAULT`."""


class Function(NamedTuple):
    """Information about a function."""

    parameters: tuple[Parameter, ...]
    """Information about the function's parameters stored as :class:`.Parameter`
    instances."""

    return_type: str | None
    """The return type for the function as a string, if present, otherwise, ``None``."""
