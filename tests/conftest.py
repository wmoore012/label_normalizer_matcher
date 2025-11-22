from __future__ import annotations

"""Test configuration for the label-normalizer-matcher package.

The package uses the ``src/`` layout. These tests should exercise the
in-repo sources rather than any globally installed version, so we prepend the
local ``src`` directory to ``sys.path``.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
