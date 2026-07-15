"""Generate and import offline Multiwfn task packages without executing Multiwfn."""

from __future__ import annotations

import fnmatch
import hashlib
import io
import json
import re
import shutil
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from werkzeug.utils import secure_filename

from .multiwfn import CHARGE_INPUTS, MultiwfnService


PROFILE_ID = "multiwfn-2026.4.10"
SCHEMA_VERSION = 1
SOURCE_EXTENSIONS = {".fchk", ".fch", ".wfn", ".wfx", ".molden", ".molden.input", ".mwfn"}
CHARGE_METHODS = tuple(CHARGE_INPUTS)


@dataclass(frozen=True, slots=True)
class ExpectedOutput:
    pattern: str
    role: str
    required: bool = True


@dataclass(frozen=True, slots=True)
class OfflineJob:
    job_id: str
    kind: str
    stdin: str
    outputs: tuple[ExpectedOutput, ...]
    parameters: dict[str, Any]
    cli_args: tuple[str, ...] = ()


class MultiwfnPackageError(ValueError):
    """A package request or imported result is invalid."""


def _safe_name(value: str, fallback: str = "source.fchk") -> str:
    name = secure_filename(Path(value).name)
    return name or fallback


def _positive_ints(value: Any, label: str) -> list[int]:
    if isinstance(value, str):
        raw = re.split(r"[,;\s]+", value.strip()) if value.strip() else []
    elif isinstance(value, (list, tuple)):
        raw = value
    elif value in (None, ""):
        raw = []
    else:
        raw = [value]
    try:
        result = [int(item) for item in raw]
    except (TypeError, ValueError) as exc:
        raise MultiwfnPackageError(f"{label} must contain integers") from exc
    if any(item <= 0 for item in result):
        raise MultiwfnPackageError(f"{label} must contain positive integers")
    return list(dict.fromkeys(result))


def _wavefunction_extension(value: str | Path) -> str:
    name = Path(value).name.lower()
    return ".molden.input" if name.endswith(".molden.input") else Path(name).suffix


def inspect_wavefunction_source(path: Path) -> dict[str, Any]:
    """Return lightweight metadata without loading the wavefunction numerically."""
    path = Path(path)
    suffix = _wavefunction_extension(path)
    if suffix not in SOURCE_EXTENSIONS:
        raise MultiwfnPackageError("Unsupported wavefunction source")
    text = path.read_text(encoding="utf-8", errors="replace")
    lower = text.lower()
    atoms = orbitals = vibrations = None
    if suffix in {".fchk", ".fch"}:
        def scalar(label: str) -> int | None:
            match = re.search(rf"^{re.escape(label)}\s+I\s+(\d+)", text, re.MULTILINE | re.IGNORECASE)
            return int(match.group(1)) if match else None
        atoms = scalar("Number of atoms")
        orbitals = scalar("Number of basis functions")
        vib_match = re.search(r"^Vib-Modes\s+R\s+N=\s*(\d+)", text, re.MULTILINE | re.IGNORECASE)
        if vib_match and atoms:
            vibrations = int(vib_match.group(1)) // max(1, atoms * 3)
        elif atoms and "vib-e2" in lower:
            vibrations = max(1, atoms * 3 - 6)
    elif suffix in {".molden", ".molden.input"}:
        sections = re.split(r"(?m)^\s*\[", text)
        atom_section = next((part for part in sections if part.lower().startswith("atoms")), "")
        atoms = len([line for line in atom_section.splitlines()[1:] if len(line.split()) >= 4]) or None
        orbitals = len(re.findall(r"(?im)^\s*ene\s*=", text)) or None
        freq = re.search(r"(?ims)^\s*\[freq\]\s*(.*?)(?=^\s*\[|\Z)", text)
        vibrations = len([line for line in freq.group(1).splitlines() if line.strip()]) if freq else None
    elif suffix == ".wfx":
        match = re.search(r"<Number of Nuclei>\s*(\d+)", text, re.IGNORECASE)
        atoms = int(match.group(1)) if match else None
        match = re.search(r"<Number of Occupied Molecular Orbitals>\s*(\d+)", text, re.IGNORECASE)
        orbitals = int(match.group(1)) if match else None
    elif suffix == ".mwfn":
        match = re.search(r"(?im)^\s*Ncenter\s*=\s*(\d+)", text)
        atoms = int(match.group(1)) if match else None
        orbitals = len(re.findall(r"(?im)^\s*Index\s*=", text)) or None
    elif suffix == ".wfn":
        match = re.search(r"(\d+)\s+NUCLEI", text, re.IGNORECASE)
        atoms = int(match.group(1)) if match else None
        match = re.search(r"(\d+)\s+MOL ORBITALS", text, re.IGNORECASE)
        orbitals = int(match.group(1)) if match else None
    return {"name": path.name, "suffix": suffix, "size": path.stat().st_size,
            "atoms": atoms, "orbitals": orbitals, "vibrations": vibrations,
            "metadata_complete": all(value is not None for value in (atoms, orbitals, vibrations))}


class MultiwfnTemplateRegistry:
    """Versioned stdin templates and expected artifact roles."""

    profiles = {
        PROFILE_ID: {
            "label": "Multiwfn 2026.4.10",
            "kinds": ["mo", "density", "esp", "nci", "igmh", "vibration", "charge"],
        }
    }

    @classmethod
    def metadata(cls) -> dict[str, Any]:
        return {"default": PROFILE_ID, "profiles": cls.profiles, "charge_methods": CHARGE_METHODS,
                "source_extensions": sorted(SOURCE_EXTENSIONS)}

    @classmethod
    def build_jobs(cls, profile: str, source_name: str, tasks: Iterable[dict[str, Any]]) -> list[OfflineJob]:
        if profile not in cls.profiles:
            raise MultiwfnPackageError(f"Unknown Multiwfn template profile: {profile}")
        source_name = _safe_name(source_name)
        if _wavefunction_extension(source_name) not in SOURCE_EXTENSIONS:
            raise MultiwfnPackageError("Source must be FCHK/FCH, WFN, WFX, Molden, or MWFN")
        jobs: list[OfflineJob] = []
        seen: set[str] = set()
        for task in tasks:
            kind = str(task.get("kind", "")).strip().lower()
            if kind == "mo":
                orbitals = _positive_ints(task.get("orbitals"), "orbitals")
                if not orbitals:
                    raise MultiwfnPackageError("MO requires at least one orbital index")
                grid = int(task.get("grid", 1))
                for orbital in orbitals:
                    jobs.append(OfflineJob(
                        f"mo_{orbital}", kind,
                        f"5\n4\n{orbital}\n{grid}\n2\n0\nq\n",
                        (ExpectedOutput("MOvalue.cub", "mo_cube"),),
                        {"orbital": orbital, "grid": grid},
                    ))
            elif kind == "density":
                grid = int(task.get("grid", 1))
                jobs.append(OfflineJob("density", kind, f"5\n1\n{grid}\n2\n0\nq\n",
                                       (ExpectedOutput("density.cub", "density_cube"),), {"grid": grid}))
            elif kind == "esp":
                iso = float(task.get("iso", 0.001))
                jobs.append(OfflineJob("esp", kind, "5\n1\n1\n2\n0\n5\n12\n1\n2\n0\nq\n",
                                       (ExpectedOutput("density.cub", "density_cube"),
                                        ExpectedOutput("totesp.cub", "esp_cube")), {"iso": iso},
                                       ("-ESPrhoiso", str(iso))))
            elif kind == "nci":
                grid = int(task.get("grid", 1))
                jobs.append(OfflineJob("nci", kind, f"20\n1\n{grid}\n2\n3\n0\n0\nq\n",
                                       (ExpectedOutput("*RDG*.cub", "surface_field"),
                                        ExpectedOutput("*signlambda2rho*.cub", "color_field")), {"grid": grid}))
            elif kind == "igmh":
                frag1, frag2 = str(task.get("fragment1", "")).strip(), str(task.get("fragment2", "")).strip()
                if not frag1 or not frag2:
                    raise MultiwfnPackageError("IGMH requires fragment1 and fragment2")
                grid = int(task.get("grid", 1))
                jobs.append(OfflineJob("igmh", kind,
                                       f"20\n11\n2\n{frag1}\n{frag2}\n{grid}\n2\n3\n0\n0\nq\n",
                                       (ExpectedOutput("dg_inter.cub", "surface_field"),
                                        ExpectedOutput("sl2r.cub", "color_field")),
                                       {"fragment1": frag1, "fragment2": frag2, "grid": grid}))
            elif kind == "vibration":
                modes = _positive_ints(task.get("modes"), "vibration modes")
                if not modes:
                    raise MultiwfnPackageError("Vibration requires at least one mode")
                frames = int(task.get("frames", 30))
                for mode in modes:
                    # Kept in the versioned profile so the sequence can evolve independently.
                    jobs.append(OfflineJob(f"vibration_{mode}", kind, f"11\n4\n{mode}\n{frames}\n0\nq\n",
                                           (ExpectedOutput("*.xyz", "vibration_xyz"),),
                                           {"mode": mode, "frames": frames}))
            elif kind == "charge":
                methods = task.get("methods") or [task.get("method", "ADCH")]
                if isinstance(methods, str):
                    methods = [item for item in re.split(r"[,;\s]+", methods) if item]
                canonical = {name.lower(): name for name in CHARGE_METHODS}
                for method_value in methods:
                    method = canonical.get(str(method_value).lower())
                    if not method:
                        raise MultiwfnPackageError(f"Unsupported charge method: {method_value}")
                    jobs.append(OfflineJob(f"charge_{method.lower()}", kind, CHARGE_INPUTS[method].lstrip("\n"),
                                           (ExpectedOutput("multiwfn.out", "charge_log"),), {"method": method}))
            else:
                raise MultiwfnPackageError(f"Unsupported task kind: {kind or '(empty)'}")
        if not jobs:
            raise MultiwfnPackageError("Select at least one Multiwfn task")
        for job in jobs:
            if job.job_id in seen:
                raise MultiwfnPackageError(f"Duplicate task: {job.job_id}")
            seen.add(job.job_id)
        return jobs


class MultiwfnPackageGenerator:
    def generate(self, source_name: str, tasks: Iterable[dict[str, Any]], output_dir: Path,
                 profile: str = PROFILE_ID, multiwfn_exe: str = "") -> tuple[Path, dict[str, Any]]:
        source_name = _safe_name(source_name)
        jobs = MultiwfnTemplateRegistry.build_jobs(profile, source_name, tasks)
        package_id = uuid.uuid4().hex[:12]
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "package_id": package_id,
            "profile": profile,
            "tool": {"multiwfn_exe": multiwfn_exe},
            "source": {"filename": source_name, "bundled": False},
            "jobs": [
                {"job_id": job.job_id, "kind": job.kind, "parameters": job.parameters,
                 "input": f"jobs/{job.job_id}/input.txt", "cli_args": list(job.cli_args),
                 "outputs": [output.__dict__ if hasattr(output, "__dict__") else {
                     "pattern": output.pattern, "role": output.role, "required": output.required
                 } for output in (job.outputs if any(o.role == "charge_log" for o in job.outputs)
                                  else job.outputs + (ExpectedOutput("multiwfn.out", "log", False),))]}
                for job in jobs
            ],
        }
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{Path(source_name).stem}_multiwfn_{package_id}.zip"
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
            archive.writestr("README_中文.txt", self._readme(source_name, profile))
            archive.writestr("run_all.bat", self._windows_launcher(jobs, multiwfn_exe))
            archive.writestr("run_all.sh", self._posix_launcher(jobs))
            for job in jobs:
                archive.writestr(f"jobs/{job.job_id}/input.txt", job.stdin)
        return path, manifest

    @staticmethod
    def _windows_launcher(jobs: list[OfflineJob], default_exe: str = "") -> str:
        default_exe = default_exe.replace('"', "") or "Multiwfn.exe"
        lines = ["@echo off", "setlocal", "if \"%~1\"==\"\" (echo Usage: run_all.bat SOURCE_FILE [MULTIWFN_EXE] & exit /b 2)",
                 "set \"SOURCE=%~f1\"", "set \"MULTIWFN=%~2\"", f"if not defined MULTIWFN set \"MULTIWFN={default_exe}\"", "set \"ROOT=%~dp0\""]
        for job in jobs:
            args = " ".join(f'\"{value}\"' for value in job.cli_args)
            lines += [f"echo Running {job.job_id}...", f"pushd \"%ROOT%jobs\\{job.job_id}\"",
                      f"\"%MULTIWFN%\" \"%SOURCE%\"{(' ' + args) if args else ''} < input.txt > multiwfn.out 2>&1",
                      "if errorlevel 1 echo WARNING: Multiwfn returned an error. See multiwfn.out", "popd"]
        return "\r\n".join(lines + ["echo All tasks finished.", "endlocal", ""]) 

    @staticmethod
    def _posix_launcher(jobs: list[OfflineJob]) -> str:
        lines = ["#!/usr/bin/env sh", "set -u", "if [ \"$#\" -lt 1 ]; then echo 'Usage: ./run_all.sh SOURCE_FILE [MULTIWFN_BIN]'; exit 2; fi",
                 "SOURCE=$1", "MULTIWFN=${2:-Multiwfn}", "ROOT=$(CDPATH= cd -- \"$(dirname -- \"$0\")\" && pwd)",
                 "case $SOURCE in /*) ;; *) SOURCE=$(CDPATH= cd -- \"$(dirname -- \"$SOURCE\")\" && pwd)/$(basename -- \"$SOURCE\");; esac"]
        for job in jobs:
            args = " ".join("'" + value.replace("'", "'\\''") + "'" for value in job.cli_args)
            lines += [f"echo 'Running {job.job_id}...'", f"(cd \"$ROOT/jobs/{job.job_id}\" && \"$MULTIWFN\" \"$SOURCE\"{(' ' + args) if args else ''} < input.txt > multiwfn.out 2>&1) || echo 'WARNING: see jobs/{job.job_id}/multiwfn.out'"]
        return "\n".join(lines + ["echo 'All tasks finished.'", ""])

    @staticmethod
    def _readme(source_name: str, profile: str) -> str:
        return (f"XYZRender Multiwfn 离线任务包\n模板：{profile}\n源文件：{source_name}（未包含在 ZIP 内）\n\n"
                "Windows: run_all.bat \"D:\\path\\source.fchk\" [Multiwfn.exe]\n"
                "Linux:   chmod +x run_all.sh && ./run_all.sh /path/source.fchk [Multiwfn]\n\n"
                "运行结束后请将整个任务包目录重新压缩，或选择 manifest.json 与 jobs 目录中的结果文件回导。\n"
                "input.txt 是可审阅、可手动调整的 Multiwfn 标准输入序列。\n")


def _single_line(value: Any, label: str) -> str:
    text = str(value or "").strip()
    if not text or any(char in text for char in "\r\n\x00"):
        raise MultiwfnPackageError(f"{label} is invalid")
    return text


class QuantumInputPackageGenerator:
    """Create calculation scripts; the application never launches the QC engine."""

    def generate(self, source_name: str, symbols: Iterable[str], coordinates: Iterable[Iterable[float]],
                 options: dict[str, Any], output_dir: Path) -> tuple[Path, dict[str, Any]]:
        engine = str(options.get("engine", "gaussian")).lower()
        if engine not in {"gaussian", "orca"}:
            raise MultiwfnPackageError("Engine must be gaussian or orca")
        functional = _single_line(options.get("functional", "B3LYP"), "functional")
        basis = _single_line(options.get("basis", "6-31G(d)"), "basis")
        charge, multiplicity = int(options.get("charge", 0)), int(options.get("multiplicity", 1))
        if multiplicity <= 0:
            raise MultiwfnPackageError("Multiplicity must be positive")
        atoms = [(str(symbol), tuple(float(v) for v in xyz)) for symbol, xyz in zip(symbols, coordinates)]
        if not atoms or any(len(xyz) != 3 for _symbol, xyz in atoms):
            raise MultiwfnPackageError("Structure has no valid atomic coordinates")
        stem = secure_filename(Path(source_name).stem) or "calculation"
        job_name = secure_filename(str(options.get("job_name", stem))) or stem
        cores = max(1, int(options.get("cores", 8)))
        memory = _single_line(options.get("memory", "8GB"), "memory")
        job_types = []
        if options.get("opt", True): job_types.append("opt")
        if options.get("freq", False): job_types.append("freq")
        if not job_types: job_types.append("sp")
        package_id = uuid.uuid4().hex[:12]
        expected = ([f"{job_name}.fchk", f"{job_name}.log"] if engine == "gaussian"
                    else [f"{job_name}.molden.input", f"{job_name}.out"])
        manifest = {"schema_version": SCHEMA_VERSION, "package_id": package_id,
                    "kind": "wavefunction_calculation", "engine": engine, "source": source_name,
                    "functional": functional, "basis": basis, "charge": charge,
                    "multiplicity": multiplicity, "job_types": job_types, "expected_results": expected}
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{job_name}_{engine}_{package_id}.zip"
        if engine == "gaussian":
            input_name = f"{job_name}.gjf"
            input_text = self._gaussian(job_name, atoms, functional, basis, charge, multiplicity,
                                        job_types, cores, memory, str(options.get("extra_route", "")))
            run_bat, run_sh = self._gaussian_launchers(job_name)
        else:
            input_name = f"{job_name}.inp"
            input_text = self._orca(job_name, atoms, functional, basis, charge, multiplicity,
                                    job_types, cores, memory, str(options.get("extra_route", "")))
            run_bat, run_sh = self._orca_launchers(job_name)
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
            archive.writestr(f"structure/{stem}.xyz", self._xyz(atoms, source_name))
            archive.writestr(input_name, input_text)
            archive.writestr("run_calculation.bat", run_bat)
            archive.writestr("run_calculation.sh", run_sh)
            archive.writestr("README_中文.txt", self._readme(engine, input_name, expected))
        return path, manifest

    @staticmethod
    def _xyz(atoms, title):
        lines = [str(len(atoms)), f"generated from {title}"]
        lines += [f"{symbol:<3s} {xyz[0]: .10f} {xyz[1]: .10f} {xyz[2]: .10f}" for symbol, xyz in atoms]
        return "\n".join(lines) + "\n"

    @staticmethod
    def _gaussian(job_name, atoms, functional, basis, charge, multiplicity, job_types, cores, memory, extra):
        route_jobs = [item for item in job_types if item != "sp"]
        route = " ".join([f"#p {functional}/{basis}", *route_jobs, "scf=xqc", "nosymm", extra.strip()]).strip()
        lines = [f"%nprocshared={cores}", f"%mem={memory}", f"%chk={job_name}.chk", route, "",
                 f"XYZRender wavefunction preparation: {job_name}", "", f"{charge} {multiplicity}"]
        lines += [f"{symbol:<3s} {xyz[0]: .10f} {xyz[1]: .10f} {xyz[2]: .10f}" for symbol, xyz in atoms]
        return "\n".join(lines) + "\n\n"

    @staticmethod
    def _orca(job_name, atoms, functional, basis, charge, multiplicity, job_types, cores, memory, extra):
        keywords = [functional, basis, "TightSCF", *[item.capitalize() for item in job_types if item != "sp"]]
        if extra.strip(): keywords.append(_single_line(extra, "extra keywords"))
        memory_match = re.match(r"\d+", memory)
        maxcore = max(128, int(memory_match.group()) * 1024 // cores) if memory_match else 1024
        lines = ["! " + " ".join(keywords), f"%pal nprocs {cores} end", f"%maxcore {maxcore}",
                 f"* xyz {charge} {multiplicity}"]
        lines += [f"  {symbol:<3s} {xyz[0]: .10f} {xyz[1]: .10f} {xyz[2]: .10f}" for symbol, xyz in atoms]
        return "\n".join(lines + ["*", ""])

    @staticmethod
    def _gaussian_launchers(job_name):
        bat = (f'@echo off\r\nset "GAUSSIAN=%~1"\r\nif not defined GAUSSIAN set "GAUSSIAN=g16"\r\n'
               f'"%GAUSSIAN%" < "{job_name}.gjf" > "{job_name}.log"\r\nif errorlevel 1 exit /b %errorlevel%\r\n'
               f'formchk "{job_name}.chk" "{job_name}.fchk"\r\n')
        sh = (f'#!/usr/bin/env sh\nset -e\nGAUSSIAN=${{1:-g16}}\n"$GAUSSIAN" < "{job_name}.gjf" > "{job_name}.log"\n'
              f'formchk "{job_name}.chk" "{job_name}.fchk"\n')
        return bat, sh

    @staticmethod
    def _orca_launchers(job_name):
        bat = (f'@echo off\r\nset "ORCA=%~1"\r\nif not defined ORCA set "ORCA=orca"\r\n'
               f'"%ORCA%" "{job_name}.inp" > "{job_name}.out"\r\nif errorlevel 1 exit /b %errorlevel%\r\n'
               f'orca_2mkl "{job_name}" -molden\r\n')
        sh = (f'#!/usr/bin/env sh\nset -e\nORCA=${{1:-orca}}\n"$ORCA" "{job_name}.inp" > "{job_name}.out"\n'
              f'orca_2mkl "{job_name}" -molden\n')
        return bat, sh

    @staticmethod
    def _readme(engine, input_name, outputs):
        engine_name = "Gaussian + formchk" if engine == "gaussian" else "ORCA + orca_2mkl"
        return (f"XYZRender 波函数计算脚本\n计算引擎：{engine_name}\n输入文件：{input_name}\n\n"
                "本应用只生成脚本，不会启动量化计算。请检查泛函、基组、电荷和多重度后再运行。\n"
                "Windows: run_calculation.bat [量化程序路径]\nLinux: chmod +x run_calculation.sh && ./run_calculation.sh [量化程序路径]\n\n"
                f"计算结束后请上传：{', '.join(outputs)}\n")


def _cube_signature(data: bytes) -> tuple[int, tuple[int, int, int], tuple[str, ...]]:
    lines = data.decode("utf-8", errors="replace").splitlines()
    if len(lines) < 6:
        raise MultiwfnPackageError("Cube file has an incomplete header")
    try:
        atoms = abs(int(lines[2].split()[0]))
        dims = tuple(abs(int(lines[i].split()[0])) for i in (3, 4, 5))
    except (ValueError, IndexError) as exc:
        raise MultiwfnPackageError("Cube file has an invalid header") from exc
    geometry = tuple(" ".join(line.split()[:5]) for line in lines[2:6])
    return atoms, dims, geometry


def _xyz_frames(data: bytes) -> tuple[int, int]:
    lines = data.decode("utf-8", errors="replace").splitlines()
    cursor, frames, atoms = 0, 0, 0
    while cursor < len(lines):
        while cursor < len(lines) and not lines[cursor].strip():
            cursor += 1
        if cursor >= len(lines):
            break
        try:
            count = int(lines[cursor].strip())
        except ValueError as exc:
            raise MultiwfnPackageError("Vibration XYZ is not a valid multi-frame XYZ") from exc
        if count <= 0 or cursor + count + 2 > len(lines):
            raise MultiwfnPackageError("Vibration XYZ contains an incomplete frame")
        atoms = atoms or count
        if count != atoms:
            raise MultiwfnPackageError("Vibration XYZ atom count changes between frames")
        frames += 1
        cursor += count + 2
    return atoms, frames


class MultiwfnArtifactStore:
    """Import, validate, list, resolve, and delete controlled CALC artifacts."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def import_payloads(self, payloads: Iterable[tuple[str, bytes]]) -> dict[str, Any]:
        files = self._expand(payloads)
        manifest_entry = next(((name, data) for name, data in files.items() if PurePosixPath(name).name == "manifest.json"), None)
        if manifest_entry:
            try:
                manifest = json.loads(manifest_entry[1].decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise MultiwfnPackageError("manifest.json is invalid") from exc
            return self._import_manifest(files, manifest)
        return self._import_inferred(files)

    @staticmethod
    def _expand(payloads: Iterable[tuple[str, bytes]]) -> dict[str, bytes]:
        files: dict[str, bytes] = {}
        for raw_name, data in payloads:
            name = _safe_name(raw_name, "upload.bin")
            if Path(name).suffix.lower() == ".zip":
                try:
                    with zipfile.ZipFile(io.BytesIO(data)) as archive:
                        if len(archive.infolist()) > 512:
                            raise MultiwfnPackageError("ZIP contains too many files")
                        total = 0
                        for info in archive.infolist():
                            path = PurePosixPath(info.filename.replace("\\", "/"))
                            if info.is_dir():
                                continue
                            if path.is_absolute() or ".." in path.parts:
                                raise MultiwfnPackageError("ZIP contains an unsafe path")
                            total += info.file_size
                            if total > 256 * 1024 * 1024:
                                raise MultiwfnPackageError("ZIP expands beyond 256 MB")
                            key = str(path)
                            if key in files:
                                raise MultiwfnPackageError(f"Duplicate imported file: {key}")
                            files[key] = archive.read(info)
                except zipfile.BadZipFile as exc:
                    raise MultiwfnPackageError("Uploaded ZIP is invalid") from exc
            else:
                if name in files:
                    raise MultiwfnPackageError(f"Duplicate imported file: {name}")
                files[name] = data
        if not files:
            raise MultiwfnPackageError("No result files supplied")
        return files

    def _import_manifest(self, files: dict[str, bytes], manifest: dict[str, Any]) -> dict[str, Any]:
        if manifest.get("schema_version") != SCHEMA_VERSION:
            raise MultiwfnPackageError("Unsupported manifest schema version")
        if manifest.get("profile") not in MultiwfnTemplateRegistry.profiles:
            raise MultiwfnPackageError("Unknown Multiwfn template profile")
        source_name = _safe_name(str((manifest.get("source") or {}).get("filename", "source.fchk")))
        source_key = secure_filename(Path(source_name).stem) or "source"
        package_id = re.sub(r"[^a-zA-Z0-9_-]", "", str(manifest.get("package_id", ""))) or uuid.uuid4().hex[:12]
        base = self.root / source_key / package_id
        imported, jobs_result = [], []
        for job in manifest.get("jobs") or []:
            job_id = secure_filename(str(job.get("job_id", "job"))) or "job"
            kind = str(job.get("kind", "unknown"))
            target = base / job_id
            target.mkdir(parents=True, exist_ok=True)
            artifacts, warnings, missing = [], [], []
            for spec in job.get("outputs") or []:
                pattern, role = str(spec.get("pattern", "")), str(spec.get("role", "artifact"))
                prefix = f"jobs/{job_id}/"
                matches = [(name, data) for name, data in files.items()
                           if (name.startswith(prefix) and fnmatch.fnmatch(PurePosixPath(name).name, pattern))]
                if not matches:
                    matches = [(name, data) for name, data in files.items() if fnmatch.fnmatch(PurePosixPath(name).name, pattern)]
                if not matches:
                    if spec.get("required", True):
                        missing.append(pattern)
                    continue
                name, data = matches[0]
                if not data:
                    missing.append(pattern)
                    continue
                filename = _safe_name(PurePosixPath(name).name, f"{role}.dat")
                if role == "charge_log":
                    method = str((job.get("parameters") or {}).get("method", "ADCH"))
                    charges = MultiwfnService.parse_charges(data.decode("utf-8", errors="replace"), method)
                    if not charges:
                        warnings.append(f"Could not parse {method} charges")
                    else:
                        filename = f"charges_{method}.txt"
                        data = "".join(f"{index}  {value:.8f}\n" for index, _symbol, value in charges).encode()
                        role = "charge_cmap"
                path = target / filename
                path.write_bytes(data)
                artifact = self._artifact(path, source_key, package_id, job_id, kind, role)
                artifacts.append(artifact); imported.append(artifact)
            warnings += self._validate_job(kind, artifacts)
            status = "ready" if not missing and not warnings else ("invalid" if missing else "warning")
            jobs_result.append({"job_id": job_id, "kind": kind, "status": status,
                                "missing": missing, "warnings": warnings, "artifacts": artifacts,
                                "binding": self._binding(kind, artifacts)})
        (base / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        result = {"ok": True, "source": source_key, "source_file": source_name, "package_id": package_id, "jobs": jobs_result,
                  "artifacts": imported, "inferred": False}
        (base / "import.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return result

    def _import_inferred(self, files: dict[str, bytes]) -> dict[str, Any]:
        package_id = uuid.uuid4().hex[:12]
        source = "inferred"
        base = self.root / source / package_id / "unclassified"
        base.mkdir(parents=True, exist_ok=True)
        artifacts = []
        for name, data in files.items():
            if not data:
                continue
            filename = _safe_name(PurePosixPath(name).name, "artifact.dat")
            lower = filename.lower()
            role = "artifact"
            if lower.endswith((".cub", ".cube")):
                role = "surface_field" if any(token in lower for token in ("rdg", "dg_inter")) else "color_field"
            elif lower.endswith(".xyz"):
                role = "vibration_xyz"
            elif "charge" in lower:
                role = "charge_cmap"
            path = base / filename; path.write_bytes(data)
            artifacts.append(self._artifact(path, source, package_id, "unclassified", "unknown", role))
        return {"ok": True, "source": source, "package_id": package_id, "jobs": [], "artifacts": artifacts,
                "inferred": True, "requires_confirmation": True}

    @staticmethod
    def _validate_job(kind: str, artifacts: list[dict[str, Any]]) -> list[str]:
        warnings: list[str] = []
        cube_artifacts = [a for a in artifacts if Path(a["name"]).suffix.lower() in {".cub", ".cube"}]
        signatures = []
        for artifact in cube_artifacts:
            try:
                signatures.append(_cube_signature(Path(artifact["path"]).read_bytes()))
            except MultiwfnPackageError as exc:
                warnings.append(str(exc))
        if kind in {"esp", "nci", "igmh"} and len(signatures) >= 2 and signatures[0][1:] != signatures[1][1:]:
            warnings.append("Paired Cube grids or geometry do not match")
        for artifact in artifacts:
            if artifact["role"] == "vibration_xyz":
                try:
                    atoms, frames = _xyz_frames(Path(artifact["path"]).read_bytes())
                    artifact["metadata"] = {"atoms": atoms, "frames": frames}
                    if frames < 2:
                        warnings.append("Vibration XYZ contains fewer than two frames")
                except MultiwfnPackageError as exc:
                    warnings.append(str(exc))
        return warnings

    def _artifact(self, path: Path, source: str, package_id: str, job_id: str, kind: str, role: str) -> dict[str, Any]:
        relative = path.relative_to(self.root).as_posix()
        digest = hashlib.sha256(relative.encode()).hexdigest()[:16]
        return {"id": f"calc:{digest}", "name": path.name, "suffix": path.suffix.lower(), "size": path.stat().st_size,
                "source": source, "package_id": package_id, "job_id": job_id, "kind": kind, "role": role,
                "relative_path": relative, "path": str(path)}

    @staticmethod
    def _binding(kind: str, artifacts: list[dict[str, Any]]) -> dict[str, Any]:
        by_role = {a["role"]: a["id"] for a in artifacts}
        if kind == "mo": return {"file_ref": by_role.get("mo_cube"), "mo": True, "format": "svg"}
        if kind == "density": return {"file_ref": by_role.get("density_cube"), "dens": True, "format": "svg"}
        if kind == "esp": return {"file_ref": by_role.get("density_cube"), "esp_ref": by_role.get("esp_cube"), "format": "svg"}
        if kind in {"nci", "igmh"}: return {"file_ref": by_role.get("color_field"), "nci_surf_ref": by_role.get("surface_field"), "format": "svg"}
        if kind == "vibration": return {"file_ref": by_role.get("vibration_xyz"), "gif_trj": True, "format": "gif"}
        if kind == "charge": return {"cmap_ref": by_role.get("charge_cmap")}
        return {}

    def list(self) -> list[dict[str, Any]]:
        result = []
        for path in self.root.rglob("*"):
            if path.is_file() and path.name not in {"manifest.json", "import.json"}:
                parts = path.relative_to(self.root).parts
                if len(parts) >= 4:
                    result.append(self._artifact(path, parts[0], parts[1], parts[2], "unknown", self._role_from_import(path)))
        return sorted(result, key=lambda item: Path(item["path"]).stat().st_mtime, reverse=True)

    def _role_from_import(self, path: Path) -> str:
        import_path = path.parents[1] / "import.json"
        if import_path.is_file():
            try:
                data = json.loads(import_path.read_text(encoding="utf-8"))
                for artifact in data.get("artifacts", []):
                    if artifact.get("relative_path") == path.relative_to(self.root).as_posix():
                        return artifact.get("role", "artifact")
            except (OSError, json.JSONDecodeError):
                pass
        return "artifact"

    def resolve(self, artifact_id: str) -> Path:
        for artifact in self.list():
            if artifact["id"] == artifact_id:
                path = Path(artifact["path"]).resolve()
                if self.root.resolve() not in path.parents:
                    break
                return path
        raise FileNotFoundError("CALC artifact not found")

    def delete_package(self, source: str, package_id: str) -> bool:
        source, package_id = secure_filename(source), secure_filename(package_id)
        target = (self.root / source / package_id).resolve()
        if self.root.resolve() not in target.parents or not target.is_dir():
            return False
        shutil.rmtree(target)
        return True

    def package_detail(self, source: str, package_id: str) -> dict[str, Any]:
        source, package_id = secure_filename(source), secure_filename(package_id)
        target = (self.root / source / package_id).resolve()
        if self.root.resolve() not in target.parents:
            raise FileNotFoundError("CALC package not found")
        detail = target / "import.json"
        if not detail.is_file():
            raise FileNotFoundError("CALC package not found")
        data = json.loads(detail.read_text(encoding="utf-8"))
        for artifact in data.get("artifacts", []):
            artifact.pop("path", None)
        for job in data.get("jobs", []):
            for artifact in job.get("artifacts", []):
                artifact.pop("path", None)
        return data
