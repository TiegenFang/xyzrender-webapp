"""应用路径解析，避免界面层和服务层各自推断项目目录。"""

from __future__ import annotations

import os
import sys
from pathlib import Path


WORKSPACE_ENV = "XYZRENDER_WORKSPACE"
USER_DATA_ENV = "XYZRENDER_USER_DATA"
APP_DATA_DIRNAME = "XYZRender Workstation"


def resolve_user_data_root() -> Path:
    """Return a per-user writable data directory.

    Desktop builds must never write beside the executable because that directory is
    normally read-only after an Inno Setup per-machine installation.
    """
    configured = os.environ.get(USER_DATA_ENV) or os.environ.get(WORKSPACE_ENV)
    if configured:
        return Path(configured).expanduser().resolve()

    local_base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
    if local_base:
        return (Path(local_base) / APP_DATA_DIRNAME).resolve()
    return (Path.home() / ".xyzrender-workstation").resolve()


def resolve_resource_root() -> Path:
    """Return the read-only application resource root in source and frozen builds."""
    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root:
        return Path(frozen_root).resolve()
    for candidate in Path(__file__).resolve().parents:
        if (candidate / "MOLECULES").is_dir() and (candidate / "pyproject.toml").is_file():
            return candidate
    return Path.cwd().resolve()


def resolve_workspace_root() -> Path:
    """返回运行数据根目录。

    优先级依次为环境变量、打包程序所在目录、源码项目根目录和当前目录。
    """
    configured = os.environ.get(WORKSPACE_ENV)
    if configured:
        return Path(configured).expanduser().resolve()
    if getattr(sys, "frozen", False):
        return resolve_user_data_root()

    for candidate in Path(__file__).resolve().parents:
        if (candidate / "app.py").is_file() and (candidate / "requirements.txt").is_file():
            return candidate
    return Path.cwd().resolve()


def ensure_runtime_directories(root: Path) -> tuple[Path, Path, Path]:
    """创建并返回分子、临时预览和正式输出目录。"""
    root = Path(root).resolve()
    directories = tuple(root / name for name in ("MOLECULES", "TEMP", "FIGURE"))
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    return directories
