"""
Traverse the AST with the ability to transform it to add templates for docstrings based
on the source code.
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING

from .visitor import DocstringVisitor

if TYPE_CHECKING:
    from ..converters import DocstringConverter
    from ..nodes.base import DocstringNode


class DocstringTransformer(ast.NodeTransformer, DocstringVisitor):
    """
    A class for indicating where docstrings are missing in a single module of source code
    and injecting suggested docstring templates based on the AST representation into the
    source code.

    Parameters
    ----------
    filename : str
        The file to process.
    converter : type[DocstringConverter]
        The converter class determines the docstring style to use for generating the
        suggested docstring templates.
    overwrite : bool, keyword-only, default=False
        Whether to save the modified source code back to the original file.
    verbose : bool, keyword-only, default=False
        Whether to run in verbose mode.
    """

    def __init__(
        self,
        filename: str,
        converter: type[DocstringConverter],
        *,
        overwrite: bool = False,
        verbose: bool = False,
    ) -> None:
        super().__init__(filename, converter, verbose=verbose)

        self.overwrite: bool = overwrite
        """Whether to save the modified source code back to the original file."""

    def save(self) -> None:
        """Save the modified AST to a file as source code."""
        if self.missing_docstrings:
            output = (
                self.source_file
                if self.overwrite
                else self.source_file.parent
                / (
                    self.source_file.stem
                    + '_docstringify'
                    + ''.join(self.source_file.suffixes)
                )
            )
            edited_code = ast.unparse(self.tree)
            output.write_text(edited_code)
            print(f'Docstring templates written to {output}')

    def handle_missing_docstring(self, docstring_node: DocstringNode) -> DocstringNode:
        """
        Handle missing docstrings by injecting a suggested docstring template based on
        the source code into the AST.

        Parameters
        ----------
        docstring_node : DocstringNode
            An instance of :class:`.DocstringNode`, which wraps an AST node and adds
            additional context relevant for Docstringify.

        Returns
        -------
        DocstringNode
            An instance of :class:`.DocstringNode`, which wraps an AST node and adds
            additional context relevant for Docstringify. The AST node it contains will
            have a new node for the docstring template added to its body.
        """
        suggested_docstring = self.docstring_converter.suggest_docstring(
            docstring_node,
            indent=0
            if isinstance(docstring_node.ast_node, ast.Module)
            else docstring_node.ast_node.col_offset + 4,
        )
        docstring_ast_node = ast.Expr(ast.Constant(suggested_docstring))

        if docstring_node.docstring is not None:
            # If the docstring is empty, we replace it with the suggested docstring
            docstring_node.ast_node.body[0] = docstring_ast_node
        else:
            # If the docstring is missing, we insert the suggested docstring
            docstring_node.ast_node.body.insert(0, docstring_ast_node)

        docstring_node.ast_node = ast.fix_missing_locations(docstring_node.ast_node)

        return docstring_node

    def process_file(self) -> None:
        """
        Process a source code file, handling missing docstrings and saving the modified
        AST to a file.
        """
        super().process_file()
        self.save()
