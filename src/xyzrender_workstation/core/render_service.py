"""基于 xyzrender Python API 的共享渲染服务。"""

from __future__ import annotations

import inspect
import json
import logging
import shlex
import tempfile
from pathlib import Path
from typing import Any, Callable

import xyzrender
from xyzrender.export import svg_to_pdf, svg_to_png

from .models import RenderRequest, RenderResult
from .option_schema import build_option_schema
from .rotation import rotate_molecule_copy


logger = logging.getLogger(__name__)


class UnsupportedRenderOption(ValueError):
    pass


def _clean(options: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in options.items() if value not in (None, "", [], {})}


class RenderService:
    def __init__(self):
        self.version = getattr(xyzrender, "__version__", "unknown")
        self.render_parameters = set(inspect.signature(xyzrender.render).parameters)
        self.gif_parameters = set(inspect.signature(xyzrender.render_gif).parameters)
        self.load_parameters = set(inspect.signature(xyzrender.load).parameters)

    def capabilities(self) -> dict[str, Any]:
        return {
            "xyzrender_version": self.version,
            "render_options": sorted(self.render_parameters - {"molecule"}),
            "gif_options": sorted(self.gif_parameters - {"molecule"}),
            "load_options": sorted(self.load_parameters - {"molecule"}),
        }

    def option_schema(self):
        """返回当前 xyzrender 版本的完整、可搜索参数目录。"""
        return build_option_schema(xyzrender.load, xyzrender.render, xyzrender.render_gif)

    def render(self, request: RenderRequest) -> RenderResult:
        try:
            request.validate()
            fmt = request.output_format.lower()
            output = Path(request.output_path).resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            load_options = self._validated_options(request.load_options, self.load_parameters, "加载")
            supported_render = self.gif_parameters if fmt == "gif" else self.render_parameters
            render_options = self._validated_options(request.render_options, supported_render, "渲染")
            molecule = xyzrender.load(str(request.source), smiles=request.smiles, **load_options)
            if request.quaternion is not None:
                molecule = rotate_molecule_copy(molecule, request.quaternion)
                render_options["orient"] = False

            command = self.diagnostic_command(request)
            if fmt == "gif":
                gif_options = self._validated_options(request.gif_options, self.gif_parameters, "GIF")
                conflicts = sorted(set(render_options) & set(gif_options))
                if conflicts:
                    raise ValueError(f"这些 GIF 参数被重复设置: {', '.join(conflicts)}")
                result = xyzrender.render_gif(molecule, **render_options, **gif_options)
                result.save(output)
            else:
                result = xyzrender.render(molecule, **render_options)
                if fmt == "svg":
                    result.save(output)
                elif fmt == "png":
                    size = int(render_options.get("canvas_size") or 800)
                    dpi = int(request.render_options.get("dpi") or 300)
                    svg_to_png(result._svg, str(output), size=size, dpi=dpi)
                elif fmt == "pdf":
                    svg_to_pdf(result._svg, str(output))
            return RenderResult(
                ok=True,
                output_path=output,
                command=command,
                diagnostics={"xyzrender_version": self.version, "format": fmt},
            )
        except Exception as exc:
            logger.error("Render service failed: %s; command=%s", exc, self.diagnostic_command(request), exc_info=True)
            return RenderResult(ok=False, error=str(exc), command=self.diagnostic_command(request))

    def preview(self, request: RenderRequest) -> RenderResult:
        preview_path = Path(tempfile.gettempdir()) / "xyzrender_workstation_preview.png"
        preview_request = RenderRequest(
            source=request.source,
            output_path=preview_path,
            output_format="png",
            smiles=request.smiles,
            load_options=dict(request.load_options),
            render_options=dict(request.render_options),
            quaternion=request.quaternion,
        )
        return self.render(preview_request)

    def diagnostic_command(self, request: RenderRequest) -> str:
        source = f"--smi {shlex.quote(str(request.source))}" if request.smiles else shlex.quote(str(request.source))
        payload = {
            "load": _clean(request.load_options),
            "render": _clean(request.render_options),
            "gif": _clean(request.gif_options),
            "quaternion": request.quaternion,
        }
        return f"xyzrender {source} -o {shlex.quote(str(request.output_path))}  # API {json.dumps(payload, ensure_ascii=False, default=str)}"

    @staticmethod
    def _validated_options(options: dict[str, Any], supported: set[str], label: str) -> dict[str, Any]:
        cleaned = _clean(options)
        cleaned.pop("dpi", None)
        unknown = sorted(set(cleaned) - supported)
        if unknown:
            raise UnsupportedRenderOption(f"当前 xyzrender 不支持这些{label}参数: {', '.join(unknown)}")
        return cleaned


def request_from_web_payload(
    payload: dict[str, Any],
    molecule_dir: Path,
    temp_dir: Path,
    artifact_resolver: Callable[[str], Path] | None = None,
) -> RenderRequest:
    """Map the stable Flask JSON shape to the shared Python API request."""
    source_name = str(payload.get("file", ""))
    source_ref = str(payload.get("file_ref", ""))
    smiles = str(payload.get("smi", "")).strip()
    if source_ref:
        if artifact_resolver is None:
            raise ValueError("CALC artifact references are not enabled")
        source = artifact_resolver(source_ref)
        source_name = source.name
    else:
        source = smiles or (molecule_dir / Path(source_name).name)
    fmt = str(payload.get("format", "svg")).lower()
    stem = "smiles_render" if smiles else Path(source_name).stem
    style = str(payload.get("style", "default"))
    output = temp_dir / f"{stem}_{style}.{fmt}"

    def number(name, cast=float):
        value = payload.get(name)
        if value in (None, ""):
            return None
        return cast(value)

    load_options = _clean({
        "charge": number("charge", int),
        "multiplicity": number("multiplicity", int),
        "bohr": payload.get("bohr") or None,
        "rebuild": payload.get("rebuild") or None,
        "mol_frame": number("mol_frame", int),
        "ts_detect": payload.get("ts") or None,
        "ts_frame": number("ts_frame", int),
        "nci_detect": payload.get("nci") or None,
        "ensemble": payload.get("ensemble") or None,
    })
    direct_map = {
        "style": "config", "canvas_size": "canvas_size", "atom_scale": "atom_scale",
        "bond_width": "bond_width", "atom_stroke_width": "atom_stroke_width",
        "bond_color": "bond_color", "bg_color": "background", "transparent": "transparent",
        "gradient": "gradient", "fog": "fog", "fog_strength": "fog_strength",
        "vdw_opacity": "vdw_opacity", "vdw_scale": "vdw_scale",
        "atom_gradient_strength": "atom_gradient_strength",
        "bond_gradient_strength": "bond_gradient_strength", "vdw_gradient": "vdw_gradient_strength",
        "no_bonds": "hide_bonds", "unbond": "unbond", "bond": "bond", "haptic": "haptic",
        "no_hy": "no_hy", "bond_orders": "bo", "no_orient": "orient",
        "mol_color": "mol_color", "idx": "idx", "stereo": "stereo",
        "stereo_style": "stereo_style", "label_size": "label_font_size",
        "cmap_palette": "cmap_palette", "cmap_symm": "cmap_symm", "cbar": "cbar",
        "vector_scale": "vector_scale", "dof": "dof", "dof_strength": "dof_strength",
        "glow": "glow", "glow_strength": "glow_strength", "iso": "iso",
        "opacity": "opacity", "surface_style": "surface_style", "mo": "mo", "dens": "dens",
        "mo_pos_color": "mo_pos_color", "mo_neg_color": "mo_neg_color",
        "mo_blur": "mo_blur", "mo_upsample": "mo_upsample", "flat_mo": "flat_mo",
        "dens_color": "dens_color", "nci_mode": "nci_mode", "nci_cutoff": "nci_cutoff",
        "hull": "hull", "hull_color": "hull_color", "hull_opacity": "hull_opacity",
        "hull_edge": "hull_edge", "hull_edge_ratio": "hull_edge_width_ratio",
        "hull_color_type": "hull_color_type", "pore": "pore", "pore_color": "pore_color",
        "pore_opacity": "pore_opacity", "overlay_color": "overlay_color",
        "align_atoms": "align_atoms", "no_cell": "no_cell", "axes": "axes",
        "axis": "axis", "ghosts": "ghosts", "cell_color": "cell_color",
        "cell_width": "cell_width", "ghost_opacity": "ghost_opacity",
    }
    int_fields = {"canvas_size", "mo_upsample"}
    float_fields = {
        "atom_scale", "bond_width", "atom_stroke_width", "fog_strength", "vdw_opacity",
        "vdw_scale", "atom_gradient_strength", "bond_gradient_strength", "vdw_gradient",
        "label_size", "vector_scale", "dof_strength", "glow_strength", "iso", "opacity",
        "mo_blur", "nci_cutoff", "hull_opacity", "hull_edge_ratio", "pore_opacity",
        "cell_width", "ghost_opacity",
    }
    render_options: dict[str, Any] = {"config": style}
    for web_name, api_name in direct_map.items():
        if web_name == "style":
            continue
        value = payload.get(web_name)
        if value in (None, "", [], {}):
            continue
        if web_name in int_fields:
            value = int(value)
        elif web_name in float_fields:
            value = float(value)
        elif web_name == "no_orient":
            value = not bool(value)
        elif web_name in {"unbond", "bond"} and isinstance(value, str):
            value = [value]
        render_options[api_name] = value
    if payload.get("hydrogens"):
        render_options["hy"] = True
    if payload.get("hy_indices"):
        render_options["hy"] = [int(v) for v in str(payload["hy_indices"]).replace(",", " ").split()]
    if payload.get("only"):
        render_options["only"] = str(payload["only"])
    if payload.get("exclude"):
        render_options["exclude"] = str(payload["exclude"])
    if payload.get("esp_file"):
        render_options["esp"] = str(molecule_dir / Path(payload["esp_file"]).name)
    if payload.get("esp_ref"):
        if artifact_resolver is None:
            raise ValueError("CALC artifact references are not enabled")
        render_options["esp"] = str(artifact_resolver(str(payload["esp_ref"])))
    if payload.get("nci_surf_file"):
        render_options["nci"] = str(molecule_dir / Path(payload["nci_surf_file"]).name)
    if payload.get("nci_surf_ref"):
        if artifact_resolver is None:
            raise ValueError("CALC artifact references are not enabled")
        render_options["nci"] = str(artifact_resolver(str(payload["nci_surf_ref"])))
    if payload.get("cmap_ref"):
        if artifact_resolver is None:
            raise ValueError("CALC artifact references are not enabled")
        render_options["cmap"] = str(artifact_resolver(str(payload["cmap_ref"])))
    if payload.get("overlay_file"):
        render_options["overlay"] = str(molecule_dir / Path(payload["overlay_file"]).name)
    if payload.get("supercell"):
        values = tuple(int(v) for v in str(payload["supercell"]).split())
        if len(values) == 3:
            render_options["supercell"] = values
    if payload.get("dpi"):
        render_options["dpi"] = int(payload["dpi"])

    gif_options = {}
    if fmt == "gif":
        gif_options = _clean({
            "gif_rot": payload.get("gif_rot") or None,
            "gif_ts": payload.get("gif_ts") or None,
            "gif_trj": payload.get("gif_trj") or None,
            "gif_diffuse": payload.get("gif_diffuse") or None,
            "gif_fps": number("gif_fps", int),
            "rot_frames": number("rot_frames", int),
            "vib_frames": number("vib_frames", int),
            "diffuse_frames": number("diffuse_frames", int),
            "diffuse_noise": number("diffuse_noise", float),
            "diffuse_bonds": payload.get("diffuse_bonds") or None,
            "diffuse_rot": number("diffuse_rot", int),
            "anchor": payload.get("anchor") or None,
        })
    handled = set(direct_map) | {
        "file", "file_ref", "format", "smi", "charge", "multiplicity", "bohr", "rebuild",
        "mol_frame", "ts", "ts_frame", "nci", "ensemble", "hydrogens",
        "hy_indices", "only", "exclude", "esp_file", "esp_ref", "nci_surf_file", "nci_surf_ref", "cmap_ref",
        "overlay_file", "supercell", "dpi", "gif_rot", "gif_ts", "gif_trj",
        "gif_diffuse", "gif_fps", "rot_frames", "vib_frames", "diffuse_frames",
        "diffuse_noise", "diffuse_bonds", "diffuse_rot", "anchor",
    }
    unknown = sorted(
        key for key, value in payload.items()
        if key not in handled and value not in (None, "", False, [], {})
    )
    if unknown:
        raise UnsupportedRenderOption(f"共享 API 尚未映射这些 Web 参数: {', '.join(unknown)}")
    return RenderRequest(
        source=source,
        output_path=output,
        output_format=fmt,
        smiles=bool(smiles),
        load_options=load_options,
        render_options=render_options,
        gif_options=gif_options,
    )
