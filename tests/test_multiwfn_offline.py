from __future__ import annotations

import io
import importlib
import json
import zipfile
from pathlib import Path

import pytest

from xyzrender_workstation.core.multiwfn_offline import (
    MultiwfnArtifactStore,
    MultiwfnPackageError,
    MultiwfnPackageGenerator,
    QuantumInputPackageGenerator,
    inspect_wavefunction_source,
)
from xyzrender_workstation.core.render_service import request_from_web_payload


def cube(value: float = 0.0) -> bytes:
    return ("cube\ncreated by test\n 2 0.0 0.0 0.0\n"
            " 2 1.0 0.0 0.0\n 2 0.0 1.0 0.0\n 2 0.0 0.0 1.0\n"
            " 1 0.0 0.0 0.0 0.0\n 1 0.0 1.0 0.0 0.0\n" +
            " ".join([str(value)] * 8) + "\n").encode()


def all_tasks():
    return [
        {"kind": "mo", "orbitals": [12, 13]},
        {"kind": "density"},
        {"kind": "esp"},
        {"kind": "nci"},
        {"kind": "igmh", "fragment1": "1-3", "fragment2": "4-6"},
        {"kind": "vibration", "modes": [2, 3], "frames": 12},
        {"kind": "charge", "methods": ["ADCH", "Hirshfeld", "Mulliken", "CM5", "SCPA", "VDD"]},
    ]


def test_package_contains_versioned_manifest_scripts_and_every_job(tmp_path):
    path, manifest = MultiwfnPackageGenerator().generate("water sample.fchk", all_tasks(), tmp_path)
    assert manifest["profile"] == "multiwfn-2026.4.10"
    assert len(manifest["jobs"]) == 14
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        assert {"manifest.json", "run_all.bat", "run_all.sh", "README_中文.txt"} <= names
        assert "water_sample.fchk" not in names
        assert "jobs/mo_12/input.txt" in names and "jobs/vibration_3/input.txt" in names
        bat = archive.read("run_all.bat").decode()
        sh = archive.read("run_all.sh").decode()
        assert '"%MULTIWFN%" "%SOURCE%"' in bat
        assert '"$MULTIWFN" "$SOURCE"' in sh
        assert '-ESPrhoiso' in bat and '-ESPrhoiso' in sh


def test_package_embeds_configured_multiwfn_path(tmp_path):
    configured = r"C:\Program Files\Multiwfn\Multiwfn.exe"
    path, manifest = MultiwfnPackageGenerator().generate(
        "water.fchk", [{"kind": "density"}], tmp_path, multiwfn_exe=configured)
    assert manifest["tool"]["multiwfn_exe"] == configured
    with zipfile.ZipFile(path) as archive:
        bat = archive.read("run_all.bat").decode()
    assert f'set "MULTIWFN={configured}"' in bat


def test_gaussian_script_package_generates_fchk_workflow(tmp_path):
    path, manifest = QuantumInputPackageGenerator().generate(
        "water.xyz", ["O", "H", "H"], [(0, 0, 0), (0, 0, 1), (0, 1, 0)],
        {"engine": "gaussian", "functional": "PBE0", "basis": "def2SVP", "charge": 0,
         "multiplicity": 1, "opt": True, "freq": True, "cores": 4, "memory": "4GB"}, tmp_path)
    assert manifest["expected_results"][0].endswith(".fchk")
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        gjf = archive.read("water.gjf").decode()
        runner = archive.read("run_calculation.bat").decode()
    assert {"water.gjf", "run_calculation.bat", "structure/water.xyz", "manifest.json"} <= names
    assert "#p PBE0/def2SVP opt freq scf=xqc nosymm" in gjf
    assert "0 1" in gjf and 'formchk "water.chk" "water.fchk"' in runner


def test_orca_script_package_generates_molden_workflow(tmp_path):
    path, manifest = QuantumInputPackageGenerator().generate(
        "water.xyz", ["O", "H", "H"], [(0, 0, 0), (0, 0, 1), (0, 1, 0)],
        {"engine": "orca", "functional": "B3LYP", "basis": "def2-SVP", "opt": False,
         "freq": False, "cores": 2, "memory": "2GB"}, tmp_path)
    assert manifest["expected_results"][0] == "water.molden.input"
    with zipfile.ZipFile(path) as archive:
        inp = archive.read("water.inp").decode()
        runner = archive.read("run_calculation.sh").decode()
    assert "! B3LYP def2-SVP TightSCF" in inp
    assert "%maxcore 1024" in inp
    assert 'orca_2mkl "water" -molden' in runner


def test_calculation_script_rejects_injected_keywords(tmp_path):
    with pytest.raises(MultiwfnPackageError, match="functional"):
        QuantumInputPackageGenerator().generate(
            "water.xyz", ["H"], [(0, 0, 0)], {"functional": "PBE0\n%chk=bad"}, tmp_path)


def test_molden_input_is_inspected_as_wavefunction(tmp_path):
    source = tmp_path / "water.molden.input"
    source.write_text("[Atoms] AU\nO 1 8 0 0 0\nH 2 1 0 0 1\n[MO]\n Ene= -0.5\n", encoding="utf-8")
    info = inspect_wavefunction_source(source)
    assert info["suffix"] == ".molden.input"
    assert info["atoms"] == 2 and info["orbitals"] == 1


@pytest.mark.parametrize("source", ["x.exe", "x.gbw", "x.xyz"])
def test_package_rejects_unsupported_sources(source, tmp_path):
    with pytest.raises(MultiwfnPackageError, match="Source must"):
        MultiwfnPackageGenerator().generate(source, [{"kind": "density"}], tmp_path)


def test_manifest_import_validates_and_binds_esp(tmp_path):
    package, manifest = MultiwfnPackageGenerator().generate("water.fchk", [{"kind": "esp"}], tmp_path)
    result_zip = io.BytesIO()
    with zipfile.ZipFile(package) as original, zipfile.ZipFile(result_zip, "w") as result:
        for name in original.namelist():
            result.writestr(name, original.read(name))
        result.writestr("jobs/esp/density.cub", cube(0.1))
        result.writestr("jobs/esp/totesp.cub", cube(-0.1))
    imported = MultiwfnArtifactStore(tmp_path / "CALC").import_payloads([("results.zip", result_zip.getvalue())])
    job = imported["jobs"][0]
    assert job["status"] == "ready"
    assert set(job["binding"]) == {"file_ref", "esp_ref", "format"}
    assert all(item["id"].startswith("calc:") for item in job["artifacts"])
    store = MultiwfnArtifactStore(tmp_path / "CALC")
    assert store.resolve(job["binding"]["file_ref"]).name == "density.cub"
    assert len(store.list()) == 2
    assert store.package_detail(imported["source"], imported["package_id"])["source_file"] == "water.fchk"
    assert store.delete_package(imported["source"], imported["package_id"])


def test_import_rejects_zip_traversal(tmp_path):
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as archive:
        archive.writestr("../escape.cub", cube())
    with pytest.raises(MultiwfnPackageError, match="unsafe path"):
        MultiwfnArtifactStore(tmp_path / "CALC").import_payloads([("bad.zip", payload.getvalue())])


def test_vibration_and_charge_import(tmp_path):
    package, _ = MultiwfnPackageGenerator().generate(
        "water.fchk", [{"kind": "vibration", "modes": [1]}, {"kind": "charge", "methods": ["ADCH"]}], tmp_path)
    xyz = b"2\nframe 1\nH 0 0 0\nH 0 0 1\n2\nframe 2\nH 0 0 .1\nH 0 0 .9\n"
    log = b"Atom 1(H ): 0.1200\nAtom 2(H ): -0.1200\n"
    payload = io.BytesIO()
    with zipfile.ZipFile(package) as original, zipfile.ZipFile(payload, "w") as result:
        for name in original.namelist():
            result.writestr(name, original.read(name))
        result.writestr("jobs/vibration_1/vibration.xyz", xyz)
        result.writestr("jobs/charge_adch/multiwfn.out", log)
    imported = MultiwfnArtifactStore(tmp_path / "CALC").import_payloads([("result.zip", payload.getvalue())])
    vib, charge = imported["jobs"]
    assert vib["artifacts"][0]["metadata"] == {"atoms": 2, "frames": 2}
    assert vib["binding"]["gif_trj"] is True
    assert charge["artifacts"][0]["role"] == "charge_cmap"
    assert "0.12000000" in Path(charge["artifacts"][0]["path"]).read_text()


def test_unknown_manifest_version_is_rejected(tmp_path):
    data = json.dumps({"schema_version": 99, "profile": "multiwfn-2026.4.10"}).encode()
    with pytest.raises(MultiwfnPackageError, match="schema version"):
        MultiwfnArtifactStore(tmp_path / "CALC").import_payloads([("manifest.json", data)])


def test_web_package_import_list_and_controlled_download(tmp_path, monkeypatch):
    web_app = importlib.import_module("xyzrender_workstation.web.app")
    monkeypatch.setattr(web_app, "MULTIWFN_PACKAGES_DIR", tmp_path / "packages")
    monkeypatch.setattr(web_app, "CALC_STORE", MultiwfnArtifactStore(tmp_path / "CALC"))
    client = web_app.app.test_client()
    package_response = client.post("/api/multiwfn/package", json={
        "source_name": "water.fchk", "tasks": [{"kind": "density"}],
    })
    assert package_response.status_code == 200
    assert package_response.data.startswith(b"PK")

    result_zip = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(package_response.data)) as original, zipfile.ZipFile(result_zip, "w") as result:
        for name in original.namelist():
            result.writestr(name, original.read(name))
        result.writestr("jobs/density/density.cub", cube())
    imported = client.post("/api/multiwfn/import", data={"files": (io.BytesIO(result_zip.getvalue()), "result.zip")},
                           content_type="multipart/form-data")
    assert imported.status_code == 200
    artifact_id = imported.get_json()["jobs"][0]["binding"]["file_ref"]
    listed = client.get("/api/calc").get_json()
    assert listed[0]["id"] == artifact_id and "path" not in listed[0]
    downloaded = client.get("/api/calc/" + artifact_id)
    assert downloaded.status_code == 200 and downloaded.data.startswith(b"cube")


def test_web_saves_tool_path_and_generates_calculation_scripts(tmp_path, monkeypatch):
    web_app = importlib.import_module("xyzrender_workstation.web.app")
    molecules = tmp_path / "MOLECULES"
    molecules.mkdir()
    (molecules / "water.xyz").write_text(
        "3\nwater\nO 0 0 0\nH 0 0 1\nH 0 1 0\n", encoding="utf-8")
    monkeypatch.setattr(web_app, "MOLECULES_DIR", molecules)
    monkeypatch.setattr(web_app, "MULTIWFN_PACKAGES_DIR", tmp_path / "packages")
    monkeypatch.setattr(web_app, "SETTINGS_FILE", tmp_path / "settings.json")
    client = web_app.app.test_client()

    saved = client.post("/api/tool-settings", json={"multiwfn_exe": r"D:\Multiwfn\Multiwfn.exe"})
    assert saved.status_code == 200
    assert client.get("/api/tool-settings").get_json()["multiwfn_exe"].endswith("Multiwfn.exe")

    response = client.post("/api/multiwfn/calculation-package", json={
        "source_name": "water.xyz", "engine": "gaussian", "functional": "M06-2X",
        "basis": "def2TZVP", "charge": 0, "multiplicity": 1, "opt": False,
    })
    assert response.status_code == 200 and response.data.startswith(b"PK")
    with zipfile.ZipFile(io.BytesIO(response.data)) as archive:
        assert "#p M06-2X/def2TZVP" in archive.read("water.gjf").decode()


def test_web_accepts_orca_molden_input_upload(tmp_path, monkeypatch):
    web_app = importlib.import_module("xyzrender_workstation.web.app")
    molecules = tmp_path / "MOLECULES"
    molecules.mkdir()
    monkeypatch.setattr(web_app, "MOLECULES_DIR", molecules)
    client = web_app.app.test_client()
    response = client.post("/api/upload", data={
        "file": (io.BytesIO(b"[Atoms] AU\nH 1 1 0 0 0\n"), "water.molden.input")
    }, content_type="multipart/form-data")
    assert response.status_code == 200
    listed = client.get("/api/molecules").get_json()
    assert listed == [{"name": "water.molden.input", "size": 23, "suffix": ".molden.input"}]


def test_calc_references_map_to_shared_renderer_without_raw_paths(tmp_path):
    density = tmp_path / "density.cub"; density.write_bytes(cube())
    esp = tmp_path / "esp.cub"; esp.write_bytes(cube())
    known = {"calc:density": density, "calc:esp": esp}
    request = request_from_web_payload(
        {"file_ref": "calc:density", "esp_ref": "calc:esp", "format": "svg", "style": "default"},
        tmp_path / "MOLECULES", tmp_path / "TEMP", known.__getitem__,
    )
    assert request.source == density
    assert request.render_options["esp"] == str(esp)
