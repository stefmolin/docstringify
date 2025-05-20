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
    def __init__(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        module_name: str,
        source_code: str,
        parent: DocstringNode,
    ) -> None:
        super().__init__(node, module_name, source_code, parent)
        self.decorators: list[str] = [
            self.get_source_segment(decorator) for decorator in node.decorator_list
        ]

        self.is_method: bool = self.parent and isinstance(
            self.parent.ast_node, ast.ClassDef
        )
        self.is_abstract_method: bool = self.is_method and (
            'abstractmethod' in self.decorators
            or 'abc.abstractmethod' in self.decorators
        )
        self.is_class_method: bool = self.is_method and 'classmethod' in self.decorators
        self.is_static_method: bool = (
            self.is_method and 'staticmethod' in self.decorators
        )
        self.is_instance_method: bool = (
            self.is_method and not self.is_class_method and not self.is_static_method
        )

        # don't require docstring for the __init__ method if the class has a docstring
        self.docstring_required: bool = not (
            self.is_method and self.name == '__init__' and self.parent.docstring
        )

        self.arguments: ast.arguments | None = getattr(node, 'args', None)
        self.return_annotation: str | None = self._extract_return_annotation()
        self.return_statements: list[ast.Return] = []

    def _extract_default_values(
        self, default: ast.Constant | None | Literal[NO_DEFAULT], is_keyword_only: bool
    ) -> str | Literal[NO_DEFAULT]:
        if (not is_keyword_only and default is not NO_DEFAULT) or (
            is_keyword_only and default
        ):
            try:
                default_value = default.value
            except AttributeError:
                default_value = f'`{default.id}`'

            return (
                f'"{default_value}"'
                if isinstance(default_value, str) and not default_value.startswith('`')
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
                type_=getattr(arg.annotation, 'id', PARAMETER_TYPE_PLACEHOLDER),
                category=None,
                default=NO_DEFAULT,
            )
            if arg
            else None
            for arg_type in ['vararg', 'kwarg']
            for arg in [getattr(self.arguments, arg_type)]
        ]

    def _extract_positional_args(self) -> list[Parameter]:
        if (default_count := len(positional_defaults := self.arguments.defaults)) < (
            positional_arguments_count := len(self.arguments.posonlyargs)
            + len(self.arguments.args)
        ):
            positional_defaults = [NO_DEFAULT] * (
                positional_arguments_count - default_count
            ) + positional_defaults

        return [
            Parameter(
                name=arg.arg,
                type_=getattr(arg.annotation, 'id', PARAMETER_TYPE_PLACEHOLDER),
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
        return [
            Parameter(
                name=arg.arg,
                type_=getattr(arg.annotation, 'id', PARAMETER_TYPE_PLACEHOLDER),
                category='keyword-only',
                default=self._extract_default_values(default, True),
            )
            for arg, default in zip(
                self.arguments.kwonlyargs, self.arguments.kw_defaults
            )
        ]

    def extract_arguments(self) -> tuple[Parameter, ...]:
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
        if return_annotation_node := self.ast_node.returns:
            if isinstance(return_annotation_node, ast.Constant):
                return return_annotation_node.value
            if isinstance(return_annotation_node, ast.Name):
                return return_annotation_node.id
            return self.get_source_segment(return_annotation_node)
        return None

    def extract_returns(self) -> str | None:
        if self.return_annotation:
            return self.return_annotation
        if any(
            not isinstance(return_value := return_node.value, ast.Constant)
            or return_value.value
            for return_node in self.return_statements
        ):
            return RETURN_TYPE_PLACEHOLDER
        return None

    def to_function(self) -> Function:
        return Function(self.extract_arguments(), self.extract_returns())
