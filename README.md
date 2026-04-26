# Docstringify
Flag missing docstrings and, optionally, generate them from signatures and type annotations.

<table>
   <tr>
     <td>
      <img alt="Last Release" src="https://img.shields.io/badge/last%20release-inactive?style=for-the-badge">
     </td>
     <td>
      <a href="https://pypi.org/project/docstringify/" target="_blank" rel="noopener noreferrer">
        <img alt="PyPI release" src="https://img.shields.io/pypi/v/docstringify.svg">
      </a>
      <a href="https://pypi.org/project/docstringify/" target="_blank" rel="noopener noreferrer">
        <img alt="Supported Python Versions" src="https://img.shields.io/pypi/pyversions/docstringify">
      </a>
      <a href="https://github.com/stefmolin/docstringify/blob/main/LICENSE" target="_blank" rel="noopener noreferrer">
         <img alt="License" src="https://img.shields.io/pypi/l/docstringify.svg?color=blueviolet">
      </a>
     </td>
   </tr>
   <tr>
     <td>
      <img alt="Build status" src="https://img.shields.io/badge/build%20status-inactive?style=for-the-badge">
     </td>
     <td>
<!--       <a href="https://codecov.io/gh/stefmolin/docstringify" target="_blank" rel="noopener noreferrer">
        <img alt="codecov" src="https://codecov.io/gh/stefmolin/docstringify/branch/main/graph/badge.svg?token=3SEEG9SZQO">
      </a> -->
      <a href="https://github.com/stefmolin/docstringify/actions/workflows/ci.yml" target="_blank" rel="noopener noreferrer">
        <img alt="CI" src="https://github.com/stefmolin/docstringify/actions/workflows/ci.yml/badge.svg">
      </a>
     </td>
   </tr>
   <tr>
     <td>
      <img alt="Downloads" src="https://img.shields.io/badge/%23downloads-inactive?style=for-the-badge">
     </td>
     <td>
      <a href="https://pypi.org/project/docstringify/" target="_blank" rel="noopener noreferrer">
        <img alt="PyPI downloads" src="https://img.shields.io/pepy/dt/docstringify?label=pypi&color=blueviolet">
      </a>
     </td>
   </tr>
  </table>

## About

Given a file, `test.py`, with the following contents:

```python
def say_hello(name: str = 'World') -> None:
    print(f'Hello, {name}!')
```

You can use Docstringify in three modes:

1. `check`: Flag missing docstrings:

    ```
    test is missing a docstring
    test.say_hello is missing a docstring
    ```
2. `suggest`: Suggest docstring templates based on type annotations:

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
3. `edit`: Add docstring templates to source code files:

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

> [!NOTE]
> The examples in this section apply to versions 2.0.0 and greater. If you are using an older version, consult the README at that tag.

#### Check mode: `docstringify-check`

Add the following to your `.pre-commit-config.yaml` file to block commits with missing docstrings before any formatters like `ruff`:

```yaml
- repo: https://github.com/stefmolin/docstringify
  rev: <version>
  hooks:
    - id: docstringify-check
```

By default, all docstrings are required. If you want to be more lenient, you can set the threshold, which is the percentage of docstrings that must be present:

```yaml
- repo: https://github.com/stefmolin/docstringify
  rev: <version>
  hooks:
    - id: docstringify-check
      args: [--threshold=0.75]
```

#### Suggest mode: `docstringify-suggest`

If you would like to see suggested docstring templates (inferred from type annotations for functions and methods), use the `suggest` mode, along with the docstring style you want to use (options are `google`, `numpydoc`, and `stub`). Here, we ask for stub suggestions (just single lines of `"""__description__"""`):

```yaml
- repo: https://github.com/stefmolin/docstringify
  rev: <version>
  hooks:
    - id: docstringify-suggest
      args: [--style=stub]
```

#### Edit mode: `docstringify-edit`

Use the `edit` mode to create a copy of each file with docstring templates. Here, we ask for changes using the [Google docstring style](https://www.sphinx-doc.org/en/master/usage/extensions/example_google.html):

```yaml
- repo: https://github.com/stefmolin/docstringify
  rev: <version>
  hooks:
    - id: docstringify-edit
      args: [--style=google]
```

If you want the changes to be made in place, add `--overwrite`. Here, we ask for [numpydoc-style docstring](https://numpydoc.readthedocs.io/en/latest/format.html#) suggestions:

```yaml
- repo: https://github.com/stefmolin/docstringify
  rev: <version>
  hooks:
    - id: docstringify-edit
      args: [--overwrite, --style=numpydoc]
```

> [!WARNING]
> Make sure you only operate on files that are in version control if you are using `--overwrite`.

Be sure to check out the [pre-commit documentation](https://pre-commit.com/#pre-commit-configyaml---hooks) for additional configuration options.

### Command line

First, install the `docstringify` package from PyPI:

```shell
$ python -m pip install docstringify
```

Then, use the `docstringify` entry point on the file(s) of your choice. For example, to run in `check` mode:

```shell
$ docstringify check /path/to/file [/path/to/another/file]
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

If you want to overwrite the file with the edits, pass `overwrite=True` to `DocstringTransformer()`:

```pycon
>>> from docstringify.converters import GoogleDocstringConverter
>>> from docstringify.traversal import DocstringTransformer
>>> transformer = DocstringTransformer(
...     'test.py', converter=GoogleDocstringConverter, overwrite=True
... )
>>> transformer.process_file()
test is missing a docstring
test.say_hello is missing a docstring
Docstring templates written to /.../test.py
```

## Contributing

Please consult the [contributing guidelines](https://github.com/stefmolin/docstringify/blob/main/CONTRIBUTING.md).
