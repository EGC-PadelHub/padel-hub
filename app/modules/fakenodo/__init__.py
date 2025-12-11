"""Fakenodo module package.

Expose the in-process blueprint for module registration.
This module provides a mock Zenodo API for testing and development.
"""

from .routes import fakenodo_module  # noqa: F401

__all__ = ["fakenodo_module"]
