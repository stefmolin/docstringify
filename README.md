# Docstringify
Flag missing docstrings and, optionally, generate them from signatures and type annotations.

## About

Given a file, `test.py`, with the following contents:

```python
def say_hello(name: str = 'World') -> None:
    print(f'Hello, {name}!')
```

You can use Docstringify in three modes:

1. Flag missing docstrings:
    ```
    test is missing a docstring
    test.say_hello is missing a docstring
    ```
2. Suggest docstring templates based on type annotations:
    ```
    test is missing a docstring
    Hint:
    """__description__"""

    test.say_hello is missing a docstring
    Hint:
    """
    __description__

    Parameters
    ----------
    name : str, default="World"
        __description__
    """
    ```
3. Add docstring templates to source code files:
    ```python
    """__description__"""

    def say_hello(name: str = 'World') -> None:
        """
        __description__

        Parameters
        ----------
        name : str, default="World"
            __description__
        """
        print(f'Hello, {name}!')
    ```

## Usage

### Pre-commit hook

Add the following to your `.pre-commit-config.yaml` file to block commits with missing docstrings:

```yaml
- repo: https://github.com/stefmolin/docstringify
  rev: 0.6.0
  hooks:
    - id: docstringify
```

By default, all docstrings are required. If you want to be more lenient, you can set the threshold, which is the percentage of docstrings that must be present:

```yaml
- repo: https://github.com/stefmolin/docstringify
  rev: 0.6.0
  hooks:
    - id: docstringify
      args: [--threshold=0.75]
```

If you would like to see suggested docstring templates (inferred from type annotations for functions and methods), provide the `--suggest-changes` argument, along with the docstring style you want to use (options are `google` and `numpydoc`). Here, we ask for [numpydoc-style docstring](https://numpydoc.readthedocs.io/en/latest/format.html#) suggestions:

```yaml
- repo: https://github.com/stefmolin/docstringify
  rev: 0.6.0
  hooks:
    - id: docstringify
      args: [--suggest-changes=numpydoc]
```

Use `--make-changes` to create a copy of each file with docstring templates. Here, we ask for changes using the [Google docstring style](https://www.sphinx-doc.org/en/master/usage/extensions/example_google.html):

```yaml
- repo: https://github.com/stefmolin/docstringify
  rev: 0.6.0
  hooks:
    - id: docstringify
      args: [--make-changes=google]
```

If you want the changes to be made in place, change `--make-changes` to `--make-changes-inplace` &ndash; make sure you only operate on files that are in version control with this setting. Note that the resulting format of your file may be a little different (spacing, newlines, *etc.*).

Be sure to check out the [pre-commit documentation](https://pre-commit.com/#pre-commit-configyaml---hooks) for additional configuration options.

### Command line

First, install the `docstringify` package from PyPI:

```shell
$ python -m pip install docstringify
```

Then, use the `docstringify` entry point on the file(s) of your choice:

```shell
$ docstringify /path/to/file [/path/to/another/file]
```

Run `docstringify --help` for more information.

### Python

First, install the `docstringify` package from PyPI:

```shell
$ python -m pip install docstringify
```

Then, use the `DocstringVisitor()` class on individual files to see spots where docstrings are missing:

```pycon
>>> from docstringify.traversal import DocstringVisitor
>>> visitor = DocstringVisitor('test.py')
>>> visitor.process_file()
test is missing a docstring
test.say_hello is missing a docstring
```

If you would like to see suggested docstring templates (inferred from type annotations for functions and methods), provide a converter:

```pycon
>>> from docstringify.converters import NumpydocDocstringConverter
>>> from docstringify.traversal import DocstringVisitor
>>> visitor = DocstringVisitor('test.py', converter=NumpydocDocstringConverter)
>>> visitor.process_file()
test is missing a docstring
Hint:
"""__description__"""

test.say_hello is missing a docstring
Hint:
"""
__description__

Parameters
----------
name : str, default="World"
    __description__
"""

```

To make changes to your files, you will need to use the `DocstringTransformer` instead. With the `DocstringTransformer`, the converter is required:

```pycon
>>> from docstringify.converters import GoogleDocstringConverter
>>> from docstringify.traversal import DocstringTransformer
>>> transformer = DocstringTransformer('test.py', converter=GoogleDocstringConverter)
>>> transformer.process_file()
test is missing a docstring
test.say_hello is missing a docstring
Docstring templates written to /.../test_docstringify.py
```

If you want to overwrite the file with the edits, pass `overwrite=True` to `DocstringTransformer()`.

## Contributing

Please consult the [contributing guidelines](https://github.com/stefmolin/docstringify/blob/main/CONTRIBUTING.md).
