from __future__ import annotations

import importlib
import io
import logging
import os
import urllib.request
from pathlib import Path

import pytest

from desktop import launcher
from desktop.launcher import LocalFlaskServer, configure_logging, prepare_runtime
from xyzrender_workstation.core import RenderRequest, RenderService
from xyzrender_workstation.paths import resolve_user_data_root


ROOT = Path(__file__).resolve().parents[1]


def test_desktop_uses_per_user_data_and_preserves_seeded_files(tmp_path, monkeypatch):
    monkeypatch.delenv("XYZRENDER_USER_DATA", raising=False)
    monkeypatch.delenv("XYZRENDER_WORKSPACE", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "LocalAppData"))
    assert resolve_user_data_root() == (tmp_path / "LocalAppData" / "XYZRender Workstation").resolve()

    resources = tmp_path / "readonly-program"
    samples = resources / "MOLECULES"
    samples.mkdir(parents=True)
    (samples / "sample.xyz").write_text("1\nseed\nH 0 0 0\n", encoding="utf-8")
    data = tmp_path / "user-data"
    runtime = prepare_runtime(data, resources)
    assert runtime.data_root != runtime.resource_root
    assert (runtime.molecules / "sample.xyz").is_file()
    (runtime.molecules / "sample.xyz").write_text("user-owned", encoding="utf-8")
    prepare_runtime(data, resources)
    assert (runtime.molecules / "sample.xyz").read_text(encoding="utf-8") == "user-owned"


def test_readonly_install_model_still_uploads_renders_and_saves(tmp_path, monkeypatch):
    runtime = prepare_runtime(tmp_path / "data", ROOT)
    web_app = importlib.import_module("xyzrender_workstation.web.app")
    monkeypatch.setattr(web_app, "BASE_DIR", runtime.data_root)
    monkeypatch.setattr(web_app, "MOLECULES_DIR", runtime.molecules)
    monkeypatch.setattr(web_app, "TEMP_DIR", runtime.temp)
    monkeypatch.setattr(web_app, "FIGURE_DIR", runtime.figures)

    client = web_app.app.test_client()
    upload = client.post(
        "/api/upload",
        data={"file": (io.BytesIO(b"1\nstandalone\nHe 0 0 0\n"), "uploaded.xyz")},
        content_type="multipart/form-data",
    )
    assert upload.status_code == 200
    rendered = client.post("/api/render", json={"file": "uploaded.xyz", "format": "svg", "style": "default"})
    assert rendered.status_code == 200
    output = rendered.get_json()["output"]
    saved = client.post("/api/save_figure", json={"name": output})
    assert saved.status_code == 200
    assert (runtime.figures / output).stat().st_size > 100
    assert not list((ROOT / "desktop").glob("uploaded*"))


@pytest.mark.parametrize(
    "source_name",
    ["caffeine.xyz", "c2SO4.pdb", "HAN.mol", "sample.sdf"],
)
def test_xyz_pdb_mol_and_sdf_base_render(source_name, tmp_path):
    if source_name == "sample.sdf":
        source = tmp_path / source_name
        source.write_text((ROOT / "MOLECULES" / "HAN.mol").read_text(encoding="utf-8") + "\n$$$$\n", encoding="utf-8")
    else:
        source = ROOT / "MOLECULES" / source_name
    result = RenderService().render(RenderRequest(source, tmp_path / f"{source.stem}.svg"))
    assert result.ok, result.error
    assert result.output_path.stat().st_size > 100


def test_svg_png_pdf_and_gif_outputs(tmp_path):
    source = ROOT / "MOLECULES" / "caffeine.xyz"
    service = RenderService()
    requests = {
        "svg": RenderRequest(source, tmp_path / "out.svg", "svg", render_options={"canvas_size": 240}),
        "png": RenderRequest(source, tmp_path / "out.png", "png", render_options={"canvas_size": 240, "dpi": 96}),
        "pdf": RenderRequest(source, tmp_path / "out.pdf", "pdf", render_options={"canvas_size": 240}),
        "gif": RenderRequest(
            source,
            tmp_path / "out.gif",
            "gif",
            render_options={"canvas_size": 180},
            gif_options={"gif_rot": "y", "rot_frames": 4, "gif_fps": 4},
        ),
    }
    signatures = {"png": b"\x89PNG", "pdf": b"%PDF", "gif": b"GIF8"}
    for fmt, request in requests.items():
        result = service.render(request)
        assert result.ok, f"{fmt}: {result.error}"
        content = result.output_path.read_bytes()
        assert len(content) > 100
        if fmt == "svg":
            assert b"<svg" in content[:500]
        else:
            assert content.startswith(signatures[fmt])


def test_bad_file_is_logged_and_next_render_still_works(tmp_path, caplog):
    service = RenderService()
    broken = tmp_path / "broken.xyz"
    broken.write_text("not-an-atom-count\n", encoding="utf-8")
    with caplog.at_level(logging.ERROR):
        failed = service.render(RenderRequest(broken, tmp_path / "broken.svg"))
    assert not failed.ok
    assert "Render service failed" in caplog.text

    healthy = service.render(RenderRequest(ROOT / "MOLECULES" / "caffeine.xyz", tmp_path / "healthy.svg"))
    assert healthy.ok


def test_local_server_is_loopback_only_and_log_is_writable(tmp_path):
    runtime = prepare_runtime(tmp_path / "data", ROOT)
    log_path = configure_logging(runtime)
    web_app = importlib.import_module("xyzrender_workstation.web.app")
    server = LocalFlaskServer(web_app.app)
    try:
        server.start()
        assert server.host == "127.0.0.1"
        with urllib.request.urlopen(f"{server.url}/api/health", timeout=2) as response:
            assert response.status == 200
    finally:
        server.stop()
    logging.getLogger("desktop-acceptance").error("diagnostic-marker")
    for handler in logging.getLogger().handlers:
        handler.flush()
    assert log_path.is_file()
    assert "diagnostic-marker" in log_path.read_text(encoding="utf-8")


def test_missing_dependency_is_named_in_diagnostic_log(tmp_path, monkeypatch):
    monkeypatch.setattr(launcher, "dependency_report", lambda: {"pywebview": "MISSING"})
    with pytest.raises(RuntimeError, match="pywebview"):
        launcher.run(tmp_path / "missing-dependency-data")
    log_path = tmp_path / "missing-dependency-data" / "logs" / "xyzrender-workstation.log"
    for handler in logging.getLogger().handlers:
        handler.flush()
    content = log_path.read_text(encoding="utf-8")
    assert "pywebview" in content and "MISSING" in content


def test_packaging_contract_preserves_user_data():
    spec = (ROOT / "desktop" / "xyzrender_workstation.spec").read_text(encoding="utf-8")
    installer = (ROOT / "desktop" / "installer.iss").read_text(encoding="utf-8")
    assert "COLLECT(" in spec and 'name="XYZRender Workstation"' in spec
    assert "web\" / \"templates" in spec and "web\" / \"static" in spec
    assert "XYZRender Workstation\\*" in installer
    assert "[UninstallDelete]" not in installer
    assert "LOCALAPPDATA" in installer
    assert "AppId={{8A784CF2-E228-45A1-B7C1-A5A51E22392B}" in installer
