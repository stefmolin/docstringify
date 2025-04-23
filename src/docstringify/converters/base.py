"""Base docstring converter."""

from __future__ import annotations

import ast
import textwrap
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from ..exceptions import InvalidDocstringError

if TYPE_CHECKING:
    from ..components import Parameter
    from ..nodes.base import DocstringNode
    from ..nodes.function import FunctionDocstringNode


class DocstringConverter(ABC):
    r"""
    Abstract base class defining the DocstringConverter API.

    Parameters
    ----------
    parameters_section_template : str
        Template string for the parameters section, e.g., ``Parameters:\n{parameters}``.
        Note that ``{parameters}`` must be present.
    returns_section_template : str
        Template string for the returns section, e.g., ``Returns:\n{returns}``.
        Note that ``{returns}`` must be present.
    quote : bool
        Whether to surround the generated docstrings in triple quotes.
    """

    def __init__(
        self,
        parameters_section_template: str,
        returns_section_template: str,
        quote: bool,
    ) -> None:
        self._parameters_section_template = parameters_section_template
        self._returns_section_template = returns_section_template
        self._quote = quote

    @abstractmethod
    def to_class_docstring(self, docstring_node: DocstringNode, indent: int) -> str:
        """
        Abstract method defining how to convert an AST node into a class docstring.

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
        pass

    @abstractmethod
    def to_function_docstring(
        self, docstring_node: FunctionDocstringNode, indent: int
    ) -> str:
        """
        Abstract method defining how to convert an AST node into a function docstring.

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
        pass

    @abstractmethod
    def to_module_docstring(self, docstring_node: DocstringNode) -> str:
        """
        Abstract method defining how to convert an AST node into a module docstring.

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
        pass

    @abstractmethod
    def format_parameter(self, parameter: Parameter) -> str:
        """
        An abstract method defining how to convert a :class:`.Parameter` instance into
        an entry in the parameters section of the docstring.

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
        pass

    def create_parameters_section(self, parameters: tuple[Parameter, ...]) -> str:
        """
        Given the parameters of a function, create the parameters section of the docstring.

        Parameters
        ----------
        parameters : tuple[Parameter, ...]
            Tuple of :class:`.Parameter` instances, which each provide information on
            individual function parameters, including their names, types, and default
            values (if present).

        Returns
        -------
        str
            The parameters section of the docstring.
        """
        if parameters:
            return self._parameters_section_template.format(
                parameters='\n'.join(
                    self.format_parameter(parameter) for parameter in parameters
                )
            )
        return ''

    @abstractmethod
    def format_return(self, return_type: str | None) -> str:
        """
        An abstract method defining how to convert a return type into an entry in the
        returns section of the docstring.

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
        pass

    def create_returns_section(self, return_type: str | None) -> str:
        """
        Given a return type name or the lack of a return (``None``), create the returns
        section of the docstring.

        Parameters
        ----------
        return_type : str | None
            The return type name for the function. This will be either a string for the
            name (e.g., ``list[str]``) or ``None``, if ``None`` is returned.

        Returns
        -------
        str
            The returns section part of the docstring.
        """
        if return_text := self.format_return(return_type):
            return self._returns_section_template.format(returns=return_text)
        return ''

    def format_docstring(self, docstring: str | list[str], indent: int) -> str:
        """
        Format the docstring with the requested level of indentation and surrounding
        triple quotes, if requested.

        Parameters
        ----------
        docstring : str | list[str]
            The docstring as a string or list of strings that form lines in the docstring.
        indent : int
            The number of spaces by which to indent the docstring.

        Returns
        -------
        str
            The docstring indented to ``indent`` spaces will be returned either as a
            quoted docstring if the converter was initialized with ``quote=True``, or an
            unquoted docstring otherwise.
        """
        quote = '"""' if self._quote else ''
        prefix = sep = ''
        if isinstance(docstring, str):
            docstring = [quote, docstring, quote]
        elif isinstance(docstring, list):
            if len(docstring) > 1:
                prefix = ' ' * indent if indent else ''
                sep = '\n'
            docstring = [quote, *docstring, f'{prefix}{quote}']
        else:
            raise InvalidDocstringError(type(docstring).__name__)

        return textwrap.indent(sep.join(docstring), prefix)

    def suggest_docstring(
        self, docstring_node: DocstringNode, indent: int = 0
    ) -> str | None:
        """
        Suggest a docstring template based on an AST node.

        Parameters
        ----------
        docstring_node : DocstringNode
            An instance of :class:`.DocstringNode`, which wraps an instance of
            :class:`ast.Module`, :class:`ast.ClassDef`, :class:`ast.FunctionDef`, or
            :class:`ast.AsyncFunctionDef`, adding additional context relevant for
            Docstringify.
        indent : int, default=0
            The number of spaces by which to indent the docstring.

        Returns
        -------
        str | None
            The suggested docstring.
        """
        if isinstance(docstring_node.ast_node, ast.AsyncFunctionDef | ast.FunctionDef):
            return (
                self.to_function_docstring(docstring_node, indent=indent)
                if docstring_node.docstring_required
                else None
            )

        if isinstance(docstring_node.ast_node, ast.Module):
            return self.to_module_docstring(docstring_node)

        return self.to_class_docstring(docstring_node, indent=indent)
