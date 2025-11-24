"""Fakenodo module package.

Deprecated standalone app removed. Expose the in-process blueprint for module
registration. Tests only need the main Flask app plus this blueprint.
"""

from .routes import fakenodo_module  # noqa: F401
