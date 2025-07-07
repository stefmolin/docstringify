"""__description__"""

from __future__ import annotations

import ast
from functools import partial
from typing import Callable, overload


class DocstringNode:
    """__description__"""

    @overload
    def __init__(
        self,
        node: ast.Module,
        module_name: str,
        source_code: str,
        parent: None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
        module_name: str,
        source_code: str,
        parent: DocstringNode,
    ) -> None: ...

    def __init__(
        self,
        node: ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef,
        module_name: str,
        source_code: str,
        parent: DocstringNode | None = None,
    ) -> None:
        """
        __description__

        Parameters
        ----------
        node : __type__
            __description__
        module_name : str
            __description__
        source_code : str
            __description__
        parent : __type__, default=None
            __description__
        """
        self.module_name: str = module_name
        self.parent: DocstringNode | None = parent
        self.docstring_required: bool = True

        self.ast_node: (
            ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
        ) = node
        self.name: str = getattr(node, 'name', self.module_name)

        self.get_source_segment: Callable[[ast.AST], str | None] = partial(
            ast.get_source_segment, source_code
        )

    @property
    def docstring(self) -> str | None:
        """
        __description__

        Returns
        -------
        str | None
            __description__
        """
        docstring = ast.get_docstring(self.ast_node)
        return docstring if docstring is None else docstring.strip()

    @property
    def fully_qualified_name(self) -> str:
        """
        __description__

        Returns
        -------
        str
            __description__
        """
        return (
            f'{self.parent.fully_qualified_name}.{self.name}'
            if self.parent
            else self.name
        )
