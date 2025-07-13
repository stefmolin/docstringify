"""
Traverse the AST with the ability to transform it to add templates for docstrings based
on the source code.
"""

from __future__ import annotations

import ast
import itertools
from textwrap import indent
from typing import TYPE_CHECKING

from ..exceptions import EmptyDocstringError
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
        """
        Convert the modified AST back to source code, preserving the original format and
        any comments.

        Returns
        -------
        str
            The original source code with the docstrings injected.
        """
        source_code = self.source_code.splitlines()
        output_lines = []
        write_line = start_line = 0
        skip_lines = None

        for missing_docstring in self.missing_docstrings:
            docstring_node = missing_docstring.ast_node.body[0]
            prefix = docstring_node.col_offset
            suffix = ''

            # write everything before docstring
            if not isinstance(missing_docstring.ast_node, ast.Module):
                # line before a code node
                skip_lines = missing_docstring.original_docstring_location

                if skip_lines:
                    start_line = skip_lines[-1]
                else:
                    # search for the start of the body code (may be comment, blank line,
                    # an empty docstring, etc.). restrict the search to between the
                    # class/function definition start and the first body item
                    search_end_line_number = missing_docstring.ast_node.body[1].lineno
                    node_source_code = missing_docstring.get_source_segment(
                        missing_docstring.ast_node
                    ).splitlines()[
                        : search_end_line_number - missing_docstring.ast_node.lineno
                    ]

                    expected_indent = ' ' * 4
                    for line_number, line in zip(
                        itertools.count(start=search_end_line_number, step=-1),
                        node_source_code[::-1],
                        strict=False,
                    ):
                        # starting from the end line of the search to the definition
                        # line, the first, non-empty line without the required indent
                        # will be the start of the body logic
                        if line and not line.startswith(expected_indent):
                            start_line = line_number
                            break

                    if start_line == missing_docstring.ast_node.body[1].lineno:
                        # the above logic handles multiline definitions, but if it is
                        # a single line and code is immediately afterward, we need to
                        # make sure to not overwrite that
                        start_line = docstring_node.lineno
                    elif (
                        skip_lines is None
                        and start_line < missing_docstring.ast_node.body[1].lineno
                    ):
                        start_line -= 1

                # handle edge case of "single line" definitions like `def test(): ...`
                if len(body := missing_docstring.ast_node.body) == 2:
                    code_node = body[1]
                    line_number = code_node.lineno - 1
                    line = source_code[line_number]

                    if line.strip() != (function_body := line[code_node.col_offset :]):
                        # if the function body is on the same line as the signature,
                        # cut it out in order to inject the docstring in the right spot
                        source_code[line_number] = source_code[line_number][
                            : code_node.col_offset
                        ].rstrip()

                        # add the logic under the docstring
                        start_line = body[1].lineno
                        suffix = function_body

            if skip_lines:
                # need to skip over the empty docstring in the original file
                # note that line numbers are one-based so we have to account for that
                # in the slicing logic
                output_lines += (
                    source_code[write_line : skip_lines[0] - 1]
                    + source_code[skip_lines[1] : start_line]
                )
            else:
                output_lines += source_code[write_line:start_line]

            # write docstring
            if not (docstring := missing_docstring.docstring):
                raise EmptyDocstringError

            output_lines.append(
                indent(
                    self.docstring_converter.format_docstring(
                        docstring.splitlines(),
                        indent=0,
                        quote=True,
                    )
                    + (f'\n{suffix}' if suffix else ''),
                    ' ' * prefix,
                )
            )

            # update current location in file
            write_line = start_line

        # write the rest of the file
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
        indent = (
            0
            if isinstance(docstring_node.ast_node, ast.Module)
            else docstring_node.ast_node.col_offset + 4
        )

        suggested_docstring = self.docstring_converter.suggest_docstring(
            docstring_node,
            indent=indent,
        )
        docstring_ast_node = ast.Expr(ast.Constant(suggested_docstring))

        if docstring_node.docstring is not None:
            # If the docstring is empty, we replace it with the suggested docstring
            docstring_node.ast_node.body[0] = docstring_ast_node
        else:
            # If the docstring is missing, we insert the suggested docstring
            docstring_node.ast_node.body.insert(0, docstring_ast_node)

        docstring_node.ast_node = ast.fix_missing_locations(docstring_node.ast_node)
        docstring_ast_node.col_offset = indent

    def process_file(self) -> None:
        """
        Process a source code file, handling missing docstrings and saving the modified
        AST to a file.
        """
        super().process_file()
        self.save()
