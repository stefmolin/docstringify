"""Test the docstring.traversal.visitor module."""

import pytest

from docstringify.traversal import DocstringVisitor


class TestDocstringVisitor:
    """Test the DocstringVisitor."""

    @pytest.mark.parametrize('file', ['function_without_args'])
    def test_process_file(self, capsys, request, file):
        """Test that DocstringVisitor.process_file() correctly processes files."""
        test_case = request.getfixturevalue(file)
        visitor = DocstringVisitor(test_case.file)
        visitor.process_file()

        assert visitor.docstrings_inspected == test_case.total_docstrings
        assert len(visitor.missing_docstrings) == len(test_case.missing_docstrings)

        stderr = capsys.readouterr().err.strip().split('\n')
        for missing_docstring in test_case.missing_docstrings:
            assert f'{missing_docstring} is missing a docstring' in stderr
