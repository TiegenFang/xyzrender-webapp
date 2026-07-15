"""安全执行外部 Multiwfn 任务的共享服务。"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
from pathlib import Path

from .models import MultiwfnJobResult, MultiwfnJobSpec, ToolSettings


ESP_INPUT = "\n5\n1\n1\n2\n0\n5\n12\n1\n2\n0\nq\n"
CHARGE_INPUTS = {
    "ADCH": "\n7\n11\n1\ny\n0\nq\n",
    "Hirshfeld": "\n7\n1\n1\ny\n0\nq\n",
    "Mulliken": "\n7\n5\n1\ny\n0\nq\n",
    "CM5": "\n7\n16\n1\ny\n0\nq\n",
    "SCPA": "\n7\n7\ny\n0\nq\n",
    "VDD": "\n7\n2\n1\ny\n0\nq\n",
}


class MultiwfnService:
    def __init__(self, settings: ToolSettings):
        self.settings = settings
        self._active_process: subprocess.Popen | None = None
        self._lock = threading.Lock()

    def doctor(self) -> tuple[bool, str]:
        path = Path(self.settings.multiwfn_path)
        if not self.settings.multiwfn_path:
            return False, "尚未配置 Multiwfn.exe 路径"
        if not path.is_file():
            return False, f"Multiwfn.exe 不存在: {path}"
        temp_dir = self.settings.resolved_temp_dir()
        try:
            temp_dir.mkdir(parents=True, exist_ok=True)
            probe = temp_dir / ".write_probe"
            probe.write_text("ok", encoding="ascii")
            probe.unlink()
        except OSError as exc:
            return False, f"任务目录不可写: {exc}"
        return True, f"Multiwfn 已配置: {path}"

    def cancel(self) -> None:
        with self._lock:
            proc = self._active_process
        if proc is None or proc.poll() is not None:
            return
        try:
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
            else:
                proc.terminate()
        except OSError:
            pass

    def run(self, job: MultiwfnJobSpec, progress=None, cancel=None) -> MultiwfnJobResult:
        ok, message = self.doctor()
        if not ok:
            return MultiwfnJobResult(False, job.kind, error=message)
        source = Path(job.fchk_path).resolve()
        if not source.is_file():
            return MultiwfnJobResult(False, job.kind, error=f"fchk 文件不存在: {source}")
        root = self.settings.resolved_temp_dir() / "jobs"
        root.mkdir(parents=True, exist_ok=True)
        work_dir = Path(tempfile.mkdtemp(prefix=f"multiwfn_{job.kind}_", dir=root))
        copied = work_dir / source.name
        shutil.copy2(source, copied)
        try:
            args, stdin_text, expected = self._build_job(job, copied)
        except Exception as exc:
            shutil.rmtree(work_dir, ignore_errors=True)
            return MultiwfnJobResult(False, job.kind, error=str(exc))
        if progress:
            progress(2, "启动 Multiwfn")
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
        try:
            proc = subprocess.Popen(
                args,
                cwd=work_dir,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=creationflags,
            )
            with self._lock:
                self._active_process = proc
            assert proc.stdin is not None
            proc.stdin.write(stdin_text)
            proc.stdin.close()
            started = time.monotonic()
            while proc.poll() is None:
                if cancel and cancel():
                    self.cancel()
                    return MultiwfnJobResult(False, job.kind, error="任务已取消", work_dir=work_dir)
                if time.monotonic() - started > job.timeout_seconds:
                    self.cancel()
                    return MultiwfnJobResult(False, job.kind, error=f"Multiwfn 超时 ({job.timeout_seconds}s)", work_dir=work_dir)
                if progress:
                    elapsed = int(time.monotonic() - started)
                    progress(min(85, 5 + elapsed // 2), f"Multiwfn 运行中 {elapsed}s")
                time.sleep(0.2)
            stdout = proc.stdout.read() if proc.stdout else ""
            stderr = proc.stderr.read() if proc.stderr else ""
            if proc.returncode not in (0, 24):
                return MultiwfnJobResult(False, job.kind, stdout=stdout, stderr=stderr,
                                         return_code=proc.returncode, error=f"Multiwfn 异常退出: {proc.returncode}", work_dir=work_dir)
            outputs = [work_dir / name for name in expected]
            missing = [path.name for path in outputs if not path.is_file()]
            if missing and job.kind != "charge":
                return MultiwfnJobResult(False, job.kind, stdout=stdout, stderr=stderr,
                                         return_code=proc.returncode, error=f"缺少输出文件: {', '.join(missing)}", work_dir=work_dir)
            if outputs and job.kind in {"esp", "mo", "igmh"}:
                try:
                    from xyzrender.cube import parse_cube
                    parsed = [parse_cube(path) for path in outputs]
                    if len(parsed) == 2 and parsed[0].grid_shape != parsed[1].grid_shape:
                        raise ValueError(f"cube 网格不一致: {parsed[0].grid_shape} != {parsed[1].grid_shape}")
                except Exception as exc:
                    return MultiwfnJobResult(False, job.kind, stdout=stdout, stderr=stderr,
                                             return_code=proc.returncode, error=f"cube 输出损坏: {exc}", work_dir=work_dir)
            final_dir = self.settings.resolved_figure_dir() / "multiwfn"
            final_dir.mkdir(parents=True, exist_ok=True)
            copied_outputs = []
            for output in outputs:
                if output.is_file():
                    destination = final_dir / f"{source.stem}_{output.name}"
                    shutil.copy2(output, destination)
                    copied_outputs.append(destination)
            charges = self.parse_charges(stdout, str(job.options.get("charge_type", "ADCH"))) if job.kind == "charge" else []
            if job.kind == "charge":
                if not charges:
                    return MultiwfnJobResult(False, job.kind, stdout=stdout, stderr=stderr,
                                             return_code=proc.returncode, error="未能从 Multiwfn 输出解析原子电荷", work_dir=work_dir)
                charge_type = str(job.options.get("charge_type", "ADCH"))
                charge_path = final_dir / f"{source.stem}_charges_{charge_type}.txt"
                charge_path.write_text("".join(f"{index}  {value:.8f}\n" for index, _symbol, value in charges), encoding="utf-8")
                copied_outputs.append(charge_path)
            if progress:
                progress(100, "任务完成")
            shutil.rmtree(work_dir, ignore_errors=True)
            return MultiwfnJobResult(True, job.kind, copied_outputs, stdout, stderr,
                                     proc.returncode, work_dir=work_dir, charges=charges)
        except FileNotFoundError:
            return MultiwfnJobResult(False, job.kind, error="无法启动 Multiwfn.exe", work_dir=work_dir)
        except OSError as exc:
            return MultiwfnJobResult(False, job.kind, error=f"Multiwfn 启动失败: {exc}", work_dir=work_dir)
        finally:
            with self._lock:
                self._active_process = None

    def _build_job(self, job: MultiwfnJobSpec, copied: Path):
        exe = str(Path(self.settings.multiwfn_path).resolve())
        if job.kind == "esp":
            return [exe, copied.name, "-ESPrhoiso", str(job.options.get("iso", 0.001))], ESP_INPUT, ["density.cub", "totesp.cub"]
        if job.kind == "mo":
            orbital = str(job.options.get("orbital", "HOMO"))
            grid = int(job.options.get("grid", 1))
            return [exe], f"\n{copied.name}\n5\n4\n{orbital}\n{grid}\n2\n0\nq\n", ["MOvalue.cub"]
        if job.kind == "igmh":
            frag1 = str(job.options.get("fragment1", "")).strip()
            frag2 = str(job.options.get("fragment2", "")).strip()
            if not frag1 or not frag2:
                raise ValueError("IGMH 需要两个非空片段")
            grid = int(job.options.get("grid", 1))
            seq = f"\n{copied.name}\n20\n11\n2\n{frag1}\n{frag2}\n{grid}\n2\n3\n0\n0\nq\n"
            return [exe], seq, ["dg_inter.cub", "sl2r.cub"]
        if job.kind == "charge":
            kind = str(job.options.get("charge_type", "ADCH"))
            if kind not in CHARGE_INPUTS:
                raise ValueError(f"不支持的电荷类型: {kind}")
            return [exe, str(copied)], CHARGE_INPUTS[kind], []
        raise ValueError(f"不支持的 Multiwfn 任务: {job.kind}")

    @staticmethod
    def parse_charges(text: str, charge_type: str):
        if charge_type == "SCPA":
            pattern = re.compile(r"Atom\s+(\d+)\(([^)]+?)\s*\)\s+Population:\s+[-\d.]+\s+Atomic charge:\s*([-\d.]+)")
        elif charge_type == "Mulliken":
            pattern = re.compile(r"Atom\s+(\d+)\((\w+)\s*\)\s+Population:\s+[-\d.]+\s+Net charge:\s*([-\d.]+)")
        else:
            pattern = re.compile(r"Atom\s+(\d+)\(([^)]+?)\s*\):\s+([-\d.]+)")
        return [(int(m.group(1)), m.group(2).strip(), float(m.group(3))) for m in pattern.finditer(text)]
