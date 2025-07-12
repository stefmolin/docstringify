"""Docstringify exceptions."""


class EmptyDocstringError(ValueError):
    """
    Raised when trying to write the modified source code back to a file if a docstring
    is somehow empty.
    """

    def __init__(self) -> None:
        super().__init__('Docstring is empty')


class InvalidDocstringError(TypeError):
    """
    Raised when trying to create a docstring with invalid input.

    Parameters
    ----------
    docstring_class : str
        The class of the docstring object. This is used for the error message.
    """

    def __init__(self, docstring_class: str) -> None:
        super().__init__(f'Expected str or list[str] docstring, got {docstring_class}')
