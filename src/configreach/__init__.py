"""ConfigReach: deterministic configuration coverage."""

from __future__ import annotations

import sys

# Python 3.11 added tomllib to the standard library. Python 3.10 uses the
# pinned tomli backport, exposed under the standard-library module name before
# importing submodules that use tomllib.
if sys.version_info < (3, 11):  # pragma: no cover - exercised by Python 3.10 CI
    import tomli as _tomllib

    sys.modules.setdefault("tomllib", _tomllib)

__version__ = "0.9.5"
