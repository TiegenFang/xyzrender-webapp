"""Run the existing Flask/HTML workstation inside a native pywebview window."""

from __future__ import annotations

import argparse
import importlib.metadata
import io
import json
import logging
import os
import shutil
import sys
import threading
import time
import urllib.request
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from pathlib import Path

from werkzeug.serving import BaseWSGIServer, make_server

# PyInstaller's windowed bootloader sets standard streams to None. xyzrender's GIF
# progress reporter writes to stdout, including from spawned frame workers.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

# Keep the launcher directly runnable from a source checkout while PyInstaller uses
# the same source directory through its ``pathex`` setting.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
if not getattr(sys, "frozen", False) and str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from xyzrender_workstation.paths import (
    WORKSPACE_ENV,
    ensure_runtime_directories,
    resolve_resource_root,
    resolve_user_data_root,
)


APP_NAME = "XYZRender Workstation"
LOG_NAME = "xyzrender-workstation.log"
SAMPLE_EXTENSIONS = {".xyz", ".pdb", ".mol", ".sdf", ".cif"}


@dataclass(frozen=True, slots=True)
class RuntimePaths:
    data_root: Path
    resource_root: Path
    molecules: Path
    temp: Path
    figures: Path
    logs: Path


def prepare_runtime(data_root: Path | None = None, resource_root: Path | None = None) -> RuntimePaths:
    """Create writable user folders and seed bundled examples without overwriting data."""
    data = (data_root or resolve_user_data_root()).expanduser().resolve()
    resources = (resource_root or resolve_resource_root()).resolve()
    molecules, temp, figures = ensure_runtime_directories(data)
    logs = data / "logs"
    logs.mkdir(parents=True, exist_ok=True)

    bundled_samples = resources / "MOLECULES"
    if bundled_samples.is_dir():
        for source in bundled_samples.iterdir():
            if source.is_file() and source.suffix.lower() in SAMPLE_EXTENSIONS:
                destination = molecules / source.name
                if not destination.exists():
                    shutil.copy2(source, destination)

    os.environ[WORKSPACE_ENV] = str(data)
    return RuntimePaths(data, resources, molecules, temp, figures, logs)


def configure_logging(paths: RuntimePaths) -> Path:
    """Configure a durable rotating log in the user data directory."""
    log_path = paths.logs / LOG_NAME
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    for handler in list(root_logger.handlers):
        if isinstance(handler, RotatingFileHandler):
            root_logger.removeHandler(handler)
            handler.close()
    handler = RotatingFileHandler(log_path, maxBytes=2_000_000, backupCount=4, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root_logger.addHandler(handler)
    logging.captureWarnings(True)
    return log_path


def dependency_report() -> dict[str, str]:
    """Return versions or actionable missing-dependency markers for startup logs."""
    report: dict[str, str] = {}
    for distribution in ("xyzrender", "xyzgraph", "Flask", "pywebview", "numpy", "ase", "rdkit"):
        try:
            report[distribution] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            report[distribution] = "MISSING"
    return report


class LocalFlaskServer:
    """Lifecycle wrapper around Werkzeug's local-only threaded WSGI server."""

    def __init__(self, flask_app, host: str = "127.0.0.1", port: int = 0):
        self.host = host
        self._server: BaseWSGIServer = make_server(host, port, flask_app, threaded=True)
        self.port = int(self._server.server_port)
        self._thread = threading.Thread(target=self._server.serve_forever, name="flask-local", daemon=True)

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def start(self, timeout: float = 15.0) -> None:
        self._thread.start()
        deadline = time.monotonic() + timeout
        last_error: Exception | None = None
        while time.monotonic() < deadline:
            try:
                with urllib.request.urlopen(f"{self.url}/api/health", timeout=0.5) as response:
                    if response.status == 200:
                        return
            except Exception as exc:  # service may still be importing native dependencies
                last_error = exc
                time.sleep(0.1)
        self.stop()
        raise RuntimeError(f"Local Flask service did not become ready: {last_error}")

    def stop(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        if self._thread.is_alive():
            self._thread.join(timeout=3)


def _show_fatal_error(message: str) -> None:
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.user32.MessageBoxW(None, message, APP_NAME, 0x10)
            return
        except Exception:
            pass
    print(message, file=sys.stderr)


def run(data_root: Path | None = None) -> int:
    paths = prepare_runtime(data_root=data_root)
    log_path = configure_logging(paths)
    logger = logging.getLogger(__name__)
    logger.info("Starting %s; frozen=%s", APP_NAME, bool(getattr(sys, "frozen", False)))
    logger.info("Runtime paths: %s", json.dumps({
        "resources": str(paths.resource_root), "data": str(paths.data_root),
        "molecules": str(paths.molecules), "temp": str(paths.temp),
        "figures": str(paths.figures), "logs": str(paths.logs),
    }, ensure_ascii=False))
    dependencies = dependency_report()
    logger.info("Dependency versions: %s", json.dumps(dependencies, ensure_ascii=False))
    missing = [name for name, version in dependencies.items() if version == "MISSING"]
    if missing:
        raise RuntimeError(f"Missing packaged dependencies: {', '.join(missing)}. See {log_path}")

    # Import only after XYZRENDER_WORKSPACE points at the writable user directory.
    import webview
    from xyzrender_workstation.web.app import app

    server = LocalFlaskServer(app)
    try:
        server.start()
        logger.info("Local Flask service ready at %s", server.url)
        webview.create_window(
            APP_NAME,
            server.url,
            width=1280,
            height=820,
            min_size=(960, 640),
            confirm_close=False,
        )
        webview.start(debug=False)
        return 0
    finally:
        server.stop()
        logger.info("Application stopped")


def run_self_test(data_root: Path | None = None) -> int:
    """Exercise the frozen Flask/render stack without opening a desktop window."""
    paths = prepare_runtime(data_root=data_root)
    log_path = configure_logging(paths)
    logger = logging.getLogger(__name__)
    report_path = paths.logs / "self-test.json"
    report: dict[str, object] = {
        "ok": False,
        "data_root": str(paths.data_root),
        "resource_root": str(paths.resource_root),
        "dependencies": dependency_report(),
        "inputs": {},
        "outputs": {},
    }
    try:
        missing = [name for name, version in report["dependencies"].items() if version == "MISSING"]
        if missing:
            raise RuntimeError(f"Missing packaged dependencies: {', '.join(missing)}")
        from xyzrender_workstation.web.app import app

        client = app.test_client()
        health = client.get("/api/health")
        if health.status_code != 200 or not health.get_json().get("ok"):
            raise RuntimeError(f"Health check failed: {health.status_code}")
        home = client.get("/")
        if home.status_code != 200 or b"XYZRender" not in home.data:
            raise RuntimeError(f"Bundled HTML check failed: {home.status_code}")

        sdf_path = paths.molecules / "desktop-self-test.sdf"
        sdf_path.write_text((paths.molecules / "HAN.mol").read_text(encoding="utf-8") + "\n$$$$\n", encoding="utf-8")
        input_names = ("caffeine.xyz", "c2SO4.pdb", "HAN.mol", sdf_path.name, "Al2O3.cif")
        for name in input_names:
            response = client.post("/api/render", json={"file": name, "format": "svg", "style": "default"})
            payload = response.get_json() or {}
            if response.status_code != 200 or not payload.get("ok"):
                raise RuntimeError(f"Input render failed for {name}: {payload.get('error', response.status_code)}")
            output_path = paths.temp / payload["output"]
            report["inputs"][Path(name).suffix.lower()] = output_path.stat().st_size

        format_payloads = {
            "svg": {},
            "png": {"canvas_size": 240, "dpi": 96},
            "pdf": {"canvas_size": 240},
            "gif": {"canvas_size": 180, "gif_rot": "y", "rot_frames": 4, "gif_fps": 4},
        }
        rendered_names: dict[str, str] = {}
        signatures = {"png": b"\x89PNG", "pdf": b"%PDF", "gif": b"GIF8"}
        for fmt, options in format_payloads.items():
            payload = {"file": "caffeine.xyz", "format": fmt, "style": "default", **options}
            response = client.post("/api/render", json=payload)
            body = response.get_json() or {}
            if response.status_code != 200 or not body.get("ok"):
                raise RuntimeError(f"Output render failed for {fmt}: {body.get('error', response.status_code)}")
            output_path = paths.temp / body["output"]
            content = output_path.read_bytes()
            valid = b"<svg" in content[:500] if fmt == "svg" else content.startswith(signatures[fmt])
            if len(content) <= 100 or not valid:
                raise RuntimeError(f"Invalid {fmt} output: {output_path}")
            report["outputs"][fmt] = len(content)
            rendered_names[fmt] = body["output"]

        upload = client.post(
            "/api/upload",
            data={"file": (io.BytesIO(b"1\nself-test upload\nHe 0 0 0\n"), "desktop-upload.xyz")},
            content_type="multipart/form-data",
        )
        if upload.status_code != 200:
            raise RuntimeError(f"Upload failed: {upload.get_json()}")
        saved = client.post("/api/save_figure", json={"name": rendered_names["png"]})
        if saved.status_code != 200 or not (paths.figures / rendered_names["png"]).is_file():
            raise RuntimeError(f"Save failed: {saved.get_json()}")

        broken = paths.molecules / "desktop-broken.xyz"
        broken.write_text("not-an-atom-count\n", encoding="utf-8")
        bad_response = client.post("/api/render", json={"file": broken.name, "format": "svg", "style": "default"})
        if bad_response.status_code < 400:
            raise RuntimeError("Malformed file unexpectedly rendered")
        if client.get("/api/health").status_code != 200:
            raise RuntimeError("Application did not survive malformed input")

        report.update({"ok": True, "html": True, "upload": True, "save": True, "bad_file_survived": True})
        logger.info("Frozen self-test passed: %s", json.dumps(report, ensure_ascii=False))
        return 0
    except Exception as exc:
        report["error"] = str(exc)
        logger.exception("Frozen self-test failed")
        return 1
    finally:
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("Self-test report: %s", report_path)
        for handler in logging.getLogger().handlers:
            handler.flush()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=f"Launch {APP_NAME}")
    parser.add_argument("--data-dir", type=Path, help="Override the per-user writable data directory")
    parser.add_argument("--self-test", action="store_true", help="Run the frozen acceptance test without opening a window")
    args = parser.parse_args(argv)
    try:
        if args.self_test:
            return run_self_test(args.data_dir)
        return run(args.data_dir)
    except Exception as exc:
        # Logging may not yet be configured, so ensure a best-effort user-data log exists.
        try:
            paths = prepare_runtime(data_root=args.data_dir)
            log_path = configure_logging(paths)
            logging.getLogger(__name__).exception("Desktop startup failed")
            detail = f"{exc}\n\nDiagnostic log:\n{log_path}"
        except Exception:
            detail = str(exc)
        _show_fatal_error(detail)
        return 1


if __name__ == "__main__":
    import multiprocessing

    multiprocessing.freeze_support()
    raise SystemExit(main())
