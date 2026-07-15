"""兼容入口：调用 ``scripts/build_html.py`` 生成 Web 模板。"""

from pathlib import Path
from runpy import run_path


if __name__ == "__main__":
    run_path(str(Path(__file__).resolve().parent / "scripts" / "build_html.py"), run_name="__main__")
