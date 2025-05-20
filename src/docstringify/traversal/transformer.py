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
            edited_code = self._convert_to_source_code()
            output.write_text(edited_code)
            print(f'Docstring templates written to {output}')

    def _convert_to_source_code(self) -> str:
        source_code = self.source_code.splitlines()
        output_lines = []
        write_line = 0

        for missing_docstring in self.missing_docstrings:
            # write everything before docstring
            if isinstance(missing_docstring.ast_node, ast.Module):
                prefix = start_line = 0
                suffix = ''
            else:
                docstring_node = missing_docstring.ast_node.body[0]
                prefix = docstring_node.col_offset + 4
                suffix = ''

                start_line = missing_docstring.ast_node.body[1].lineno - 1
                if isinstance(missing_docstring.ast_node, ast.ClassDef):
                    start_line -= 1

                if len(body := missing_docstring.ast_node.body) == 2:
                    code_node = body[1]
                    line_number = code_node.lineno - 1
                    line = source_code[line_number]

                    if line.strip() != (function_body := line[code_node.col_offset :]):
                        # if the function body is on the same line as the signature, cut it out
                        # in order to inject the docstring in the right spot
                        source_code[line_number] = source_code[line_number][
                            : code_node.col_offset
                        ].rstrip()

                        # add the logic under the docstring
                        start_line = missing_docstring.ast_node.body[1].lineno
                        suffix = function_body

            output_lines += source_code[write_line:start_line]

            # write docstring
            output_lines += [
                f'{" " * prefix}"""{missing_docstring.raw_docstring}"""'
                + (f'\n{" " * prefix}{suffix}' if suffix else '')
            ]
            write_line = start_line

        output_lines += source_code[write_line:]

        return '\n'.join(output_lines) + '\n'

    def handle_missing_docstring(self, docstring_node: DocstringNode) -> None:
        """
        Handle missing docstrings by injecting a suggested docstring template based on
        the source code into the AST.

        Parameters
        ----------
        docstring_node : DocstringNode
            An instance of :class:`.DocstringNode`, which wraps an AST node and adds
            additional context relevant for Docstringify.
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

    def process_file(self) -> None:
        """
        Process a source code file, handling missing docstrings and saving the modified
        AST to a file.
        """
        super().process_file()
        self.save()
