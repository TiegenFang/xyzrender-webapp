"""共享请求、结果和工具配置模型。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Literal


Quaternion = tuple[float, float, float, float]
ProgressCallback = Callable[[int, str], None]
CancelCallback = Callable[[], bool]


@dataclass(slots=True)
class RenderRequest:
    source: str | Path
    output_path: str | Path
    output_format: Literal["svg", "png", "pdf", "gif"] = "svg"
    smiles: bool = False
    load_options: dict[str, Any] = field(default_factory=dict)
    render_options: dict[str, Any] = field(default_factory=dict)
    gif_options: dict[str, Any] = field(default_factory=dict)
    quaternion: Quaternion | None = None

    def validate(self) -> None:
        fmt = self.output_format.lower()
        if fmt not in {"svg", "png", "pdf", "gif"}:
            raise ValueError(f"不支持的输出格式: {fmt}")
        if not self.smiles and not Path(self.source).is_file():
            raise FileNotFoundError(f"输入文件不存在: {self.source}")
        if self.smiles and not str(self.source).strip():
            raise ValueError("SMILES 不能为空")
        surface_keys = ("mo", "dens", "esp", "nci")
        enabled = [key for key in surface_keys if self.render_options.get(key)]
        if len(enabled) > 1:
            raise ValueError("MO、电子密度、ESP 和 NCI 表面不能同时启用")
        if fmt != "gif" and self.gif_options:
            raise ValueError("GIF 参数只能用于 GIF 输出")
        if self.quaternion is not None and len(self.quaternion) != 4:
            raise ValueError("视角四元数必须包含 4 个数值")


@dataclass(slots=True)
class RenderResult:
    ok: bool
    output_path: Path | None = None
    command: str = ""
    warnings: list[str] = field(default_factory=list)
    error: str = ""
    diagnostics: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ToolSettings:
    multiwfn_path: str = ""
    project_dir: Path = Path.cwd()
    temp_dir: Path | None = None
    figure_dir: Path | None = None

    def resolved_temp_dir(self) -> Path:
        return self.temp_dir or self.project_dir / "TEMP"

    def resolved_figure_dir(self) -> Path:
        return self.figure_dir or self.project_dir / "FIGURE"


@dataclass(slots=True)
class MultiwfnJobSpec:
    kind: Literal["esp", "mo", "igmh", "charge"]
    fchk_path: str | Path
    options: dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 900


@dataclass(slots=True)
class MultiwfnJobResult:
    ok: bool
    kind: str
    output_files: list[Path] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
    return_code: int | None = None
    error: str = ""
    work_dir: Path | None = None
    charges: list[tuple[int, str, float]] = field(default_factory=list)
