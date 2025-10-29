"""Dataset type registry and helpers for modular dataset types.

This package contains base classes and per-type implementations (e.g. tabular/CSV)
so dataset-specific logic can live separately from the platform logic.
"""

from .base import BaseDataset
from .tabular import TabularDataset

__all__ = ["BaseDataset", "TabularDataset"]
