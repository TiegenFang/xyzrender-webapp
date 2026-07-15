"""兼容入口：实际 Flask 应用位于 ``src/xyzrender_workstation/web``。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from xyzrender_workstation.web.app import app, main  # noqa: E402

__all__ = ["app", "main"]


if __name__ == "__main__":
    main()
