"""Base Docstringify traversal node."""

from __future__ import annotations

import ast
from functools import partial
from typing import Callable, overload


class DocstringNode:
    """
    Base class for Docstringify traversal nodes.

    Parameters
    ----------
    node : ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
        AST node representing a module, class, or function.
    module_name : str
        The name of the module to which the node belongs.
    source_code : str
        The source code for the module from which ``node`` originates.
    parent : DocstringNode | None, default=None
        The parent node, if there is one.
    """

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
        self.module_name: str = module_name
        """The name of the module to which the node belongs."""

        self.parent: DocstringNode | None = parent
        """The parent node, if there is one."""

        self.docstring_required: bool = True
        """Whether the node requires a docstring."""

        self.ast_node: (
            ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef
        ) = node
        """The AST node that represents the source code."""

        self.name: str = getattr(node, 'name', self.module_name)
        """The name of the node."""

        self.get_source_segment: Callable[[ast.AST], str | None] = partial(
            ast.get_source_segment, source_code
        )
        """Callable to get the source code for the AST node (:attr:`.ast_node`)."""

        self.original_docstring_location: tuple[int, int] | None = (
            None
            if self.docstring is None
            else (self.ast_node.body[0].lineno, self.ast_node.body[0].end_lineno)
        )
        """Start and end line of the docstring in the original file, if there was one,
        otherwise, ``None``. This is necessary for the rewriting algorithm to exclude
        lines containing "empty" docstrings from the file. Empty docstrings are empty
        strings or strings containing only whitespace characters."""

    @property
    def docstring(self) -> str | None:
        """
        Get the docstring from the AST node.

        Returns
        -------
        str | None
            The docstring, if it exists.
        """
        docstring = ast.get_docstring(self.ast_node)
        return docstring if docstring is None else docstring.strip()

    @property
    def fully_qualified_name(self) -> str:
        """
        Unambiguous name for the node.

        Returns
        -------
        str
            The fully-qualified name.
        """
        return (
            f'{self.parent.fully_qualified_name}.{self.name}'
            if self.parent
            else self.name
        )
