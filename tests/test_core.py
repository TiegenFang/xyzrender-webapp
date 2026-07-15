from pathlib import Path

import numpy as np
import pytest
import xyzrender

from xyzrender_workstation.core import OptionSpec, RenderRequest, RenderService, parse_option_value
from xyzrender_workstation.core.rotation import axis_angle_quaternion, rotate_molecule_copy
from xyzrender_workstation.paths import ensure_runtime_directories, resolve_workspace_root


ROOT = Path(__file__).resolve().parents[1]


def test_workspace_path_contract(tmp_path):
    assert resolve_workspace_root() == ROOT
    molecules, temp, figure = ensure_runtime_directories(tmp_path)
    assert [path.name for path in (molecules, temp, figure)] == ["MOLECULES", "TEMP", "FIGURE"]
    assert all(path.is_dir() for path in (molecules, temp, figure))


def test_complete_xyzrender_parameter_schema():
    service = RenderService()
    schema = service.option_schema()
    render_names = {item.name for item in schema if item.scope == "render"}
    assert render_names == service.render_parameters - {"molecule", "output"}
    assert {"overlay", "regions", "cmap", "vector", "hull", "supercell"} <= render_names
    supercell = OptionSpec("render", "测试", "supercell", None, "tuple[int, int, int]")
    gradient = OptionSpec("render", "测试", "gradient", True, "bool")
    assert parse_option_value(supercell, "[2, 2, 1]") == (2, 2, 1)
    assert parse_option_value(gradient, "false") is False


def pair_distances(molecule):
    positions = np.asarray([data["position"] for _, data in molecule.graph.nodes(data=True)], dtype=float)
    return np.linalg.norm(positions[:, None, :] - positions[None, :, :], axis=2)


def test_quaternion_rotation_preserves_distances():
    molecule = xyzrender.load(ROOT / "MOLECULES" / "caffeine.xyz")
    rotated = rotate_molecule_copy(molecule, axis_angle_quaternion((0, 1, 0), 0.77))
    assert np.allclose(pair_distances(molecule), pair_distances(rotated), atol=1e-9)


def test_render_service_svg_and_png(tmp_path):
    service = RenderService()
    source = ROOT / "MOLECULES" / "caffeine.xyz"
    svg = service.render(RenderRequest(source, tmp_path / "caffeine.svg", render_options={"config": "default"}))
    png = service.render(RenderRequest(source, tmp_path / "caffeine.png", output_format="png",
                                       render_options={"config": "flat", "canvas_size": 320}))
    assert svg.ok and svg.output_path.stat().st_size > 100
    assert png.ok and png.output_path.stat().st_size > 100


def test_surface_modes_are_mutually_exclusive(tmp_path):
    request = RenderRequest(ROOT / "MOLECULES" / "caffeine.xyz", tmp_path / "bad.svg",
                            render_options={"mo": True, "dens": True})
    with pytest.raises(ValueError, match="不能同时"):
        request.validate()


def test_unknown_option_is_actionable(tmp_path):
    result = RenderService().render(RenderRequest(
        ROOT / "MOLECULES" / "caffeine.xyz", tmp_path / "bad.svg",
        render_options={"not_a_real_option": True},
    ))
    assert not result.ok
    assert "不支持" in result.error
