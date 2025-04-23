"""Numpydoc-style docstring converter."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..components import DESCRIPTION_PLACEHOLDER, NO_DEFAULT, Parameter
from .base import DocstringConverter

if TYPE_CHECKING:
    from ..nodes.base import DocstringNode
    from ..nodes.function import FunctionDocstringNode


class NumpydocDocstringConverter(DocstringConverter):
    """
    Class defining the DocstringConverter API for `Numpydoc-style docstrings
    <https://numpydoc.readthedocs.io/en/latest/format.html#>`_.

    Parameters
    ----------
    quote : bool
        Whether to surround the generated docstrings in triple quotes.
    """

    def __init__(self, quote: bool) -> None:
        super().__init__(
            parameters_section_template='Parameters\n----------\n{parameters}',
            returns_section_template='Returns\n-------\n{returns}',
            quote=quote,
        )

    def to_function_docstring(
        self, docstring_node: FunctionDocstringNode, indent: int
    ) -> str:
        """
        Convert an AST node into a function docstring.

        Parameters
        ----------
        docstring_node : FunctionDocstringNode
            An instance of :class:`.FunctionDocstringNode`, which wraps an instance of
            :class:`ast.FunctionDef` or :class:`ast.AsyncFunctionDef`, adding additional
            context relevant for Docstringify.
        indent : int
            The number of spaces by which to indent the docstring.

        Returns
        -------
        str
            The function docstring.
        """
        function = docstring_node.to_function()

        docstring = [DESCRIPTION_PLACEHOLDER]

        if parameters_section := self.create_parameters_section(function.parameters):
            docstring.extend(['', parameters_section])

        if returns_section := self.create_returns_section(function.return_type):
            docstring.extend(['', returns_section])

        return self.format_docstring(docstring, indent=indent)

    def format_parameter(self, parameter: Parameter) -> str:
        """
        Convert a :class:`.Parameter` instance into an entry in the parameters section
        of the docstring.

        Parameters
        ----------
        parameter : Parameter
            Information on the function parameter, including its name, type, and default
            value (if it has one).

        Returns
        -------
        str
            An entry for the parameter for use in the parameters section of the docstring.
        """
        return (
            f'{parameter.name} : {parameter.type_}'
            f'{f", {parameter.category}" if parameter.category else ""}'
            f'{f", default={parameter.default}" if parameter.default != NO_DEFAULT else ""}'
            f'\n    {DESCRIPTION_PLACEHOLDER}'
        )

    def format_return(self, return_type: str | None) -> str:
        """
        Convert a return type into an entry in the returns section of the docstring.

        Parameters
        ----------
        return_type : str | None
            The return type name for the function. This will be either a string for the
            name (e.g., ``list[str]``) or ``None``, if ``None`` is returned.

        Returns
        -------
        str
            The return type entry for use in the returns section of the docstring.
        """
        if return_type:
            return f'{return_type}\n    {DESCRIPTION_PLACEHOLDER}'
        return ''

    def to_module_docstring(self, docstring_node: DocstringNode) -> str:
        """
        Convert an AST node into a module docstring.

        Parameters
        ----------
        docstring_node : DocstringNode
            An instance of :class:`.DocstringNode`, which wraps an instance of
            :class:`ast.Module`, adding additional context relevant for Docstringify.

        Returns
        -------
        str
            The module docstring.
        """
        return self.format_docstring(DESCRIPTION_PLACEHOLDER, indent=0)

    def to_class_docstring(self, docstring_node: DocstringNode, indent: int) -> str:
        """
        Convert an AST node into a class docstring.

        Parameters
        ----------
        docstring_node : DocstringNode
            An instance of :class:`.DocstringNode`, which wraps an instance of
            :class:`ast.ClassDef`, adding additional context relevant for Docstringify.
        indent : int
            The number of spaces by which to indent the docstring.

        Returns
        -------
        str
            The class docstring.
        """
        return self.format_docstring(DESCRIPTION_PLACEHOLDER, indent=indent)
