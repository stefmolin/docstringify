"""
Traverse the AST, indicating where docstrings are missing and suggesting templates
based on the AST.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from ..nodes.base import DocstringNode
from ..nodes.function import FunctionDocstringNode

if TYPE_CHECKING:
    from ..converters import DocstringConverter


class DocstringVisitor(ast.NodeVisitor):
    """
    A class for indicating where docstrings are missing in a single module of source code
    and suggesting templates based on the AST representation.

    Parameters
    ----------
    filename : str
        The file to process.
    converter : type[DocstringConverter] | None, optional
        When this is ``None``, docstrings will be reported as missing, but when this is
        a converter, docstring templates will be generated.
    verbose : bool, keyword-only, default=False
        Whether to run in verbose mode.
    """

    def __init__(
        self,
        filename: str,
        converter: type[DocstringConverter] | None = None,
        *,
        verbose: bool = False,
    ) -> None:
        self.source_file: Path = Path(filename).expanduser().resolve()
        """The ``Path`` object for the source file."""

        self.source_code: str = self.source_file.read_text()
        """The source code in :attr:`.source_file` as a string."""

        self.tree: ast.Module = ast.parse(self.source_code)
        """The AST for the source code in :attr:`.source_code`."""

        self.docstrings_inspected: int = 0
        """The number of docstrings inspected."""

        self.missing_docstrings: list[DocstringNode] = []
        """The list of docstrings that are missing, each represented as a :class:`.DocstringNode` instance."""

        self.module_name: str = self.source_file.stem
        """The name of the module, derived from the source file name (see :attr:`.source_file`)."""

        self.stack: list[DocstringNode] = []
        """The stack of docstring nodes, used to track the current context in the AST."""

        self.docstring_converter: DocstringConverter | None = (
            converter(quote=not issubclass(self.__class__, ast.NodeTransformer))
            if converter
            else None
        )
        """The docstring converter, if templates are to be generated, otherwise ``None``."""

        self.verbose: bool = verbose
        """Whether to run in verbose mode."""

    def report_missing_docstrings(self) -> None:
        """
        Report missing docstrings.

        See Also
        --------
        :meth:`.handle_missing_docstring`
            This method is called for each missing docstring, and it defines any actions
            that should be taken upon nodes with missing docstrings, such as, suggesting
            a docstring template based on the source code.
        """
        if self.missing_docstrings:
            for docstring_node in self.missing_docstrings:
                print(
                    f'{docstring_node.fully_qualified_name} is missing a docstring',
                    file=sys.stderr,
                )
                self.handle_missing_docstring(docstring_node)
        elif self.verbose:
            print(f'No missing docstrings found in {self.source_file}.')

    def handle_missing_docstring(self, docstring_node: DocstringNode) -> None:
        """
        Handle missing docstrings by suggesting a template for them when a converter is provided.

        Parameters
        ----------
        docstring_node : DocstringNode
            An instance of :class:`.DocstringNode`, which wraps an AST node and adds
            additional context relevant for Docstringify.
        """
        if self.docstring_converter:
            print(
                'Hint:',
                self.docstring_converter.suggest_docstring(docstring_node),
                '',
                sep='\n',
            )

    def process_docstring(self, docstring_node: DocstringNode) -> DocstringNode:
        """
        Process a docstring node, appending it to :attr:`.missing_docstrings` if a docstring
        is required, but there isn't one.

        Parameters
        ----------
        docstring_node : DocstringNode
            An instance of :class:`.DocstringNode`, which wraps an AST node and adds
            additional context relevant for Docstringify.

        Returns
        -------
        DocstringNode
            An instance of :class:`.DocstringNode`, which wraps an AST node and adds
            additional context relevant for Docstringify.
        """
        if docstring_node.docstring_required and (not docstring_node.docstring):
            self.missing_docstrings.append(docstring_node)

        self.docstrings_inspected += 1
        return docstring_node

    def visit_docstring(
        self,
        node: ast.AsyncFunctionDef | ast.ClassDef | ast.FunctionDef | ast.Module,
        docstring_class: type[DocstringNode],
    ) -> ast.AsyncFunctionDef | ast.ClassDef | ast.FunctionDef | ast.Module:
        """
        Visit an AST node by updating the stack and processing the docstring.

        Parameters
        ----------
        node : ast.AsyncFunctionDef | ast.ClassDef | ast.FunctionDef | ast.Module
            The AST node to visit.
        docstring_class : type[DocstringNode]
            The class to use for creating the docstring node.

        Returns
        -------
        ast.AsyncFunctionDef | ast.ClassDef | ast.FunctionDef | ast.Module
            The AST node that was visited.
        """
        docstring_node = docstring_class(
            node,
            self.module_name,
            self.source_code,
            parent=self.stack[-1] if self.stack else None,
        )

        self.stack.append(docstring_node)

        docstring_node = self.process_docstring(docstring_node)
        self.generic_visit(docstring_node.ast_node)
        self.stack.pop()
        return docstring_node.ast_node

    def visit_Module(self, node: ast.Module) -> ast.Module:  # noqa: N802
        """
        Visit an :class:`ast.Module` node.

        Parameters
        ----------
        node : ast.Module
            The AST node to visit.

        Returns
        -------
        ast.Module
            The visited AST node.
        """
        return self.visit_docstring(node, DocstringNode)

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:  # noqa: N802
        """
        Visit an :class:`ast.ClassDef` node.

        Parameters
        ----------
        node : ast.ClassDef
            The AST node to visit.

        Returns
        -------
        ast.ClassDef
            The visited AST node.
        """
        return self.visit_docstring(node, DocstringNode)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:  # noqa: N802
        """
        Visit an :class:`ast.FunctionDef` node.

        Parameters
        ----------
        node : ast.FunctionDef
            The AST node to visit.

        Returns
        -------
        ast.FunctionDef
            The visited AST node.
        """
        return self.visit_docstring(node, FunctionDocstringNode)

    def visit_AsyncFunctionDef(  # noqa: N802
        self, node: ast.AsyncFunctionDef
    ) -> ast.AsyncFunctionDef:
        """
        Visit an :class:`ast.AsyncFunctionDef` node.

        Parameters
        ----------
        node : ast.AsyncFunctionDef
            The AST node to visit.

        Returns
        -------
        ast.AsyncFunctionDef
            The visited AST node.
        """
        return self.visit_docstring(node, FunctionDocstringNode)

    def visit_Return(self, node: ast.Return) -> ast.Return:  # noqa: N802
        """
        Visit an :class:`ast.Return` node.

        Parameters
        ----------
        node : ast.Return
            The AST node to visit.

        Returns
        -------
        ast.Return
            The visited AST node.
        """
        if isinstance(self.stack[-1], FunctionDocstringNode):
            self.stack[-1].return_statements.append(node)
        return node

    def process_file(self) -> None:
        """Process a source code file, reporting on the missing docstrings."""
        self.visit(self.tree)
        self.report_missing_docstrings()
