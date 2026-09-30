"""ConfigReach: deterministic configuration coverage."""

from __future__ import annotations

import sys

# Python 3.11 added tomllib to the standard library. ConfigReach supports
# Python 3.8-3.10 with the pinned tomli backport and exposes it under the
# standard-library module name before importing submodules that use tomllib.
if sys.version_info < (3, 11):  # pragma: no cover - exercised by old-version CI
    import tomli as _tomllib

    sys.modules.setdefault("tomllib", _tomllib)

__version__ = "0.9.3"
