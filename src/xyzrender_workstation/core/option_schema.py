"""xyzrender 公共参数目录与桌面文本值解析。"""

from __future__ import annotations

import ast
import inspect
import json
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True, slots=True)
class OptionSpec:
    scope: str
    group: str
    name: str
    default: Any
    annotation: str
    help: str = ""


GROUPS = {
    "input": "输入与解析",
    "style": "样式与画布",
    "display": "原子与化学键",
    "surface": "表面与孔洞",
    "overlay": "叠加与区域",
    "annotation": "标签、测量与矢量",
    "interaction": "过渡态与相互作用",
    "crystal": "晶体与周期结构",
    "animation": "GIF 动画",
    "other": "其他",
}

STYLE = {
    "config", "canvas_size", "atom_scale", "bond_width", "atom_stroke_width",
    "bond_color", "bond_outline_color", "bond_outline_width", "background",
    "transparent", "gradient", "hue_shift_factor", "light_shift_factor",
    "saturation_shift_factor", "fog", "fog_strength", "atom_gradient_strength",
    "bond_gradient_strength", "vdw_gradient_strength", "mol_color",
}
DISPLAY = {
    "radius_scale", "atom_opacity", "vdw_opacity", "vdw_scale", "hide_bonds",
    "unbond", "bond", "haptic", "hy", "no_hy", "bo", "only", "exclude",
    "vdw", "bond_color_by_element", "bond_gradient", "dof", "dof_strength",
    "glow", "glow_strength", "orient", "ref",
}
SURFACE = {
    "opacity", "mo", "dens", "esp", "nci", "iso", "mo_pos_color",
    "mo_neg_color", "mo_blur", "mo_upsample", "mo_outline_width",
    "mo_outline_color", "flat_mo", "dens_color", "nci_mode", "nci_cutoff",
    "surface_style", "hull", "hull_color", "hull_opacity", "hull_edge",
    "hull_edge_width_ratio", "hull_color_type", "pore", "ring_max_size",
    "ring_min_size", "face_planarity", "pore_color", "pore_opacity",
}
OVERLAY = {
    "overlay", "overlay_color", "overlay_config", "align_atoms", "auto_align",
    "highlight", "regions",
}
ANNOTATION = {
    "idx", "cmap", "cmap_range", "cmap_palette", "cmap_symm", "cbar",
    "labels", "label_file", "label_font_size", "stereo", "stereo_style",
    "vector", "vector_scale", "vector_color",
}
INTERACTION = {
    "ts_bonds", "nci_bonds", "ts_color", "ts_element", "ts_dash", "ts_width",
    "nci_color", "nci_element", "nci_dash", "nci_width", "detect_nci",
}
CRYSTAL = {
    "cell", "no_cell", "axes", "axis", "supercell", "ghosts", "cell_color",
    "cell_width", "ghost_opacity",
}
ANIMATION = {
    "gif_rot", "gif_bounce", "gif_trj", "gif_ts", "gif_diffuse",
    "diffuse_frames", "diffuse_noise", "diffuse_bonds", "diffuse_rot",
    "diffuse_reverse", "anchor", "gif_fps", "rot_frames", "vib_frames",
    "ts_frame", "trj_bonds", "reference_graph",
}

HELP = {
    "radius_scale": "JSON 列表，例如 [[\"1-5\", 1.4]]",
    "atom_opacity": "JSON 列表，例如 [[\"1-5\", 0.3]]",
    "unbond": "JSON 列表或一个选择器，例如 [\"1-3\", \"M-L\"]",
    "bond": "JSON 键对列表，例如 [[1, 3], [4, 5]]",
    "ts_bonds": "JSON 键对列表，例如 [[1, 6], [3, 4]]",
    "nci_bonds": "JSON 键对列表，例如 [[1, 5], [2, 8]]",
    "highlight": "选择器或 JSON，例如 [[\"1-5\", \"gold\"]]",
    "regions": "JSON，例如 [[\"1-5\", \"flat\"]]",
    "cmap": "属性文件路径或 {\"1\": 0.2, \"2\": -0.1}",
    "cmap_range": "两个数，例如 [-1, 1]",
    "vector": "矢量 JSON 文件路径或 JSON 对象/列表",
    "supercell": "三个整数，例如 [2, 2, 1]",
    "axis": "晶向，例如 111",
    "gif_bounce": "角度或角度,轴，例如 50,xy",
    "hy": "true 表示全部，或原子选择器/JSON 列表",
    "hull": "true、rings、faces、pores 或索引列表",
}


def _group_for(scope: str, name: str) -> str:
    if scope == "load":
        return GROUPS["input"]
    if scope == "gif" or name in ANIMATION:
        return GROUPS["animation"]
    for names, group in (
        (STYLE, "style"), (DISPLAY, "display"), (SURFACE, "surface"),
        (OVERLAY, "overlay"), (ANNOTATION, "annotation"),
        (INTERACTION, "interaction"), (CRYSTAL, "crystal"),
    ):
        if name in names:
            return GROUPS[group]
    return GROUPS["other"]


def build_option_schema(
    load_fn: Callable[..., Any],
    render_fn: Callable[..., Any],
    gif_fn: Callable[..., Any],
) -> list[OptionSpec]:
    """从当前安装版本的公开 API 动态构建参数目录。"""
    render_names = set(inspect.signature(render_fn).parameters)
    entries: list[OptionSpec] = []
    for scope, fn in (("load", load_fn), ("render", render_fn), ("gif", gif_fn)):
        for name, parameter in inspect.signature(fn).parameters.items():
            if name in {"molecule", "output"}:
                continue
            if scope == "gif" and name in render_names:
                continue
            default = None if parameter.default is inspect.Parameter.empty else parameter.default
            annotation = "" if parameter.annotation is inspect.Parameter.empty else str(parameter.annotation)
            entries.append(OptionSpec(scope, _group_for(scope, name), name, default, annotation, HELP.get(name, "")))
    return entries


def parse_option_value(spec: OptionSpec, raw: str) -> Any:
    """把完整参数面板中的文本转换为 API 所需类型。"""
    text = raw.strip()
    if not text:
        raise ValueError(f"{spec.name} 不能为空")
    lowered = text.lower()
    if lowered in {"true", "yes", "on", "是"}:
        return True
    if lowered in {"false", "no", "off", "否"}:
        return False
    if lowered in {"none", "null"}:
        return None

    annotation = spec.annotation.lower()
    structured = any(token in annotation for token in ("list", "tuple", "dict")) or text[:1] in "[{(\"'"
    if structured:
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            try:
                value = ast.literal_eval(text)
            except (ValueError, SyntaxError) as exc:
                raise ValueError(f"{spec.name} 需要合法 JSON/Python 字面量: {exc}") from exc
        if "tuple" in annotation and isinstance(value, list):
            return tuple(value)
        return value
    if isinstance(spec.default, int) and not isinstance(spec.default, bool):
        return int(text)
    if isinstance(spec.default, float):
        return float(text)
    if "bool" in annotation and "str" not in annotation:
        raise ValueError(f"{spec.name} 是布尔参数，请填写 true 或 false")
    if "int" in annotation and "float" not in annotation and "str" not in annotation:
        return int(text)
    if "float" in annotation and "str" not in annotation:
        return float(text)
    return text
