"""geno-surf — Chromium orchestration for the geno agent (the `surf` CLI).

Browser half of geno-tt: drives a dedicated Chromium over the DevTools Protocol,
addressed by the same object-notation registry. Safari stays human."""

__version__ = "0.2.0"

from .cli import main

__all__ = ["main", "__version__"]
