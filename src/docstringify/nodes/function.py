"""Docstringify traversal node for functions."""

from __future__ import annotations

import ast
import itertools
from typing import Literal

from ..components import (
    NO_DEFAULT,
    PARAMETER_TYPE_PLACEHOLDER,
    RETURN_TYPE_PLACEHOLDER,
    Function,
    Parameter,
)
from .base import DocstringNode


class FunctionDocstringNode(DocstringNode):
    """
    Class for Docstringify function traversal nodes.

    Parameters
    ----------
    node : ast.FunctionDef | ast.AsyncFunctionDef
        AST node representing a function.
    module_name : str
        The name of the module to which the node belongs.
    source_code : str
        The source code for the module from which ``node`` originates.
    parent : DocstringNode
        The parent node.
    """

    def __init__(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        module_name: str,
        source_code: str,
        parent: DocstringNode,
    ) -> None:
        super().__init__(node, module_name, source_code, parent)

        self.decorators: list[str] = [
            decorator
            for decorator_node in node.decorator_list
            if (decorator := self.get_source_segment(decorator_node))
        ]
        """List of decorators applied to this function."""

        self.is_overload: bool = (
            'overload' in self.decorators or 'typing.overload' in self.decorators
        )
        """Whether this function definition is actually just a typing overload
        definition, and, therefore, doesn't need a docstring."""

        self.is_method: bool = self.parent is not None and isinstance(
            self.parent.ast_node, ast.ClassDef
        )
        """Whether this function is actually a method, meaning that its parent node
        is a class."""

        self.is_abstract_method: bool = self.is_method and (
            'abstractmethod' in self.decorators
            or 'abc.abstractmethod' in self.decorators
        )
        """Whether this function is an abstract method, meaning it is a method
        (:attr:`.is_method`) and has an ``abstractmethod`` decorator."""

        self.is_class_method: bool = self.is_method and 'classmethod' in self.decorators
        """Whether this function is a class method, meaning it is a method
        (:attr:`.is_method`) and has a ``classmethod`` decorator."""

        self.is_static_method: bool = (
            self.is_method and 'staticmethod' in self.decorators
        )
        """Whether this function is a static method, meaning it is a method
        (:attr:`.is_method`) and has a ``staticmethod`` decorator."""

        self.is_instance_method: bool = (
            self.is_method
            and (not self.is_class_method)
            and (not self.is_static_method)
        )
        """Whether this function is an instance method, meaning it is a method
        (:attr:`.is_method`), but it is not a class method (:attr:`.is_class_method`)
        or static method (:attr:`.is_static_method`)."""

        # don't require docstring for the __init__ method if the class has a docstring
        # or if the function/method is just a typing.overload signature
        self.docstring_required: bool = (
            not (
                self.is_method
                and self.name == '__init__'
                and self.parent is not None
                and self.parent.docstring
            )
            and not self.is_overload
        )
        """Whether this node should have a docstring. Docstrings are currently required
        for all functions unless they are a typing overload. Note that ``__init__()``
        methods don't require a docstring if the parent (the class) has a docstring."""

        self.arguments: ast.arguments = node.args
        """The function arguments in their AST representation."""

        self.returns: ast.AST | None = node.returns
        """The function's return annotation, as an AST node, if there is a return
        annotation, otherwise ``None``."""

        self.return_annotation: str | None = self._extract_return_annotation()
        """The function's return annotation, as a string, if there is a return
        annotation, otherwise ``None``."""

        self.return_statements: list[ast.Return] = []
        """All ``return`` calls in the function itself (not any inner functions, for
        example), represented as AST nodes. Note that this will be populated by the
        traversal logic when those nodes are visited."""

    def _extract_parameter_type(self, arg: ast.arg) -> str:
        """
        Extract the parameter's type.

        Parameters
        ----------
        arg : ast.arg
            The AST node for the function argument.

        Returns
        -------
        str
            The parameter type for use in the docstring.
        """
        if arg.annotation is None:
            return PARAMETER_TYPE_PLACEHOLDER

        try:
            # if `arg.annotation` is of type `ast.Name`, we can just get the `id`
            return arg.annotation.id
        except AttributeError:
            return self.get_source_segment(arg.annotation) or PARAMETER_TYPE_PLACEHOLDER

    def _extract_default_values(
        self, default: ast.Constant | None | Literal[NO_DEFAULT], is_keyword_only: bool
    ) -> str | Literal[NO_DEFAULT]:
        """
        Extract the argument's default value.

        Parameters
        ----------
        default : ast.Constant | None | Literal[NO_DEFAULT]
            The representation of the default value for further processing.
        is_keyword_only : bool
            Whether the default value being extracted corresponds to a keyword-only
            argument.

        Returns
        -------
        str | Literal[NO_DEFAULT]
            The default value as a string, if there is one, otherwise,
            :const:`.NO_DEFAULT`.
        """
        if (not is_keyword_only and default is not NO_DEFAULT) or (
            is_keyword_only and default
        ):
            try:
                default_value = default.value
            except AttributeError:
                default_value = f'`{default.id}`'

            return (
                f'"{default_value}"'
                if isinstance(default_value, str)
                and (not default_value.startswith('`'))
                else default_value
            )
        return NO_DEFAULT

    def _extract_star_args(self) -> list[Parameter | None]:
        """
        Extract the function's ``*args`` and ``**kwargs`` arguments.

        Returns
        -------
        list[Parameter | None]
            A list of the form ``[*args, **kwargs]``, where each entry is either a
            :class:`.Parameter` instance, or ``None`` if that type of argument isn't
            part of the function definition.
        """
        return [
            Parameter(
                name=f'*{arg.arg}' if arg_type == 'vararg' else f'**{arg.arg}',
                type_=self._extract_parameter_type(arg),
                category=None,
                default=NO_DEFAULT,
            )
            if arg
            else None
            for arg_type in ['vararg', 'kwarg']
            for arg in [getattr(self.arguments, arg_type)]
        ]

    def _extract_positional_args(self) -> list[Parameter]:
        """
        Extract the function's positional arguments.

        Returns
        -------
        list[Parameter]
            A list of :class:`.Parameter` instances, representing the function's
            positional arguments.
        """
        if (default_count := len(positional_defaults := self.arguments.defaults)) < (
            positional_arguments_count := (
                len(self.arguments.posonlyargs) + len(self.arguments.args)
            )
        ):
            positional_defaults = [NO_DEFAULT] * (
                positional_arguments_count - default_count
            ) + positional_defaults

        return [
            Parameter(
                name=arg.arg,
                type_=self._extract_parameter_type(arg),
                category=category,
                default=self._extract_default_values(default, False),
            )
            for (arg, category), default in zip(
                itertools.chain(
                    zip(
                        self.arguments.posonlyargs, itertools.repeat('positional-only')
                    ),
                    zip(self.arguments.args, itertools.repeat(None)),
                ),
                positional_defaults,
            )
        ]

    def _extract_keyword_args(self) -> list[Parameter]:
        """
        Extract the function's keyword arguments.

        Returns
        -------
        list[Parameter]
            A list of :class:`.Parameter` instances, representing the function's
            keyword arguments.
        """
        return [
            Parameter(
                name=arg.arg,
                type_=self._extract_parameter_type(arg),
                category='keyword-only',
                default=self._extract_default_values(default, True),
            )
            for arg, default in zip(
                self.arguments.kwonlyargs, self.arguments.kw_defaults
            )
        ]

    def extract_arguments(self) -> tuple[Parameter, ...]:
        """
        Extract the function's arguments.

        Returns
        -------
        tuple[Parameter, ...]
            A tuple of :class:`.Parameter` instances, representing all of the
            function's arguments.
        """
        params = self._extract_positional_args()

        varargs, kwargs = self._extract_star_args()

        if varargs:
            params.append(varargs)

        params.extend(self._extract_keyword_args())

        if kwargs:
            params.append(kwargs)

        params = tuple(params)
        if params and (
            (self.is_class_method and params[0].name == 'cls')
            or (self.is_instance_method and params[0].name == 'self')
        ):
            return params[1:]
        return params

    def _extract_return_annotation(self) -> str | None:
        """
        Extract the function's return annotation, if present.

        Returns
        -------
        str | None
            The return annotation as a string, if present, otherwise, ``None``.
        """
        if self.returns is None:
            return self.returns

        if isinstance(self.returns, ast.Constant):
            return self.returns.value

        if isinstance(self.returns, ast.Name):
            return self.returns.id

        return self.get_source_segment(self.returns)

    def extract_returns(self) -> str | None:
        """
        Extract the function's return type for use in the docstring.

        Returns
        -------
        str | None
            The return type as a string, if present. Otherwise, the function will
            be checked for ``return`` calls, and, if present, a placeholder for the
            type will be returned; if it isn't present, ``None``, will be returned.
        """
        if self.return_annotation:
            return self.return_annotation

        if any(
            not isinstance((return_value := return_node.value), ast.Constant)
            or return_value.value
            for return_node in self.return_statements
        ):
            return RETURN_TYPE_PLACEHOLDER

        return None

    def to_function(self) -> Function:
        """
        Convert node into a :class:`.Function` instance.

        Returns
        -------
        Function
            The :class:`.Function` instance.
        """
        return Function(self.extract_arguments(), self.extract_returns())
