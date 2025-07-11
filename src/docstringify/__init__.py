"""
Flag missing docstrings and, optionally, generate them from signatures and
type annotations.
"""

import importlib.metadata

__version__ = importlib.metadata.version(__name__)

__all__ = ['__version__']
