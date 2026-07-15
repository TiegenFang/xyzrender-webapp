import sys
import time

from xyzrender_workstation.core import MultiwfnJobSpec, MultiwfnService, ToolSettings


class FakeMultiwfnService(MultiwfnService):
    def __init__(self, settings, script, expected):
        super().__init__(settings)
        self.script = script
        self.expected = expected

    def _build_job(self, job, copied):
        return [sys.executable, str(self.script)], "", self.expected


def test_charge_parser_all_common_shapes():
    adch = "Final atomic charges:\n Atom 1(C ): -0.125\n Atom 2(H ): 0.125\n"
    mulliken = "Net charge:\n Atom 1(C ) Population: 6.2 Net charge: -0.2\n"
    scpa = "Atom 1(C ) Population: 6.1 Atomic charge: -0.1\n"
    assert MultiwfnService.parse_charges(adch, "ADCH") == [(1, "C", -0.125), (2, "H", 0.125)]
    assert MultiwfnService.parse_charges(mulliken, "Mulliken") == [(1, "C", -0.2)]
    assert MultiwfnService.parse_charges(scpa, "SCPA") == [(1, "C", -0.1)]


def test_doctor_reports_missing_executable(tmp_path):
    service = MultiwfnService(ToolSettings(str(tmp_path / "Multiwfn.exe"), tmp_path))
    ok, message = service.doctor()
    assert not ok
    assert "不存在" in message


def test_igmh_requires_two_fragments(tmp_path):
    fake_exe = tmp_path / "Multiwfn.exe"
    fake_exe.write_bytes(b"")
    fchk = tmp_path / "sample.fchk"
    fchk.write_text("placeholder", encoding="ascii")
    service = MultiwfnService(ToolSettings(str(fake_exe), tmp_path))
    result = service.run(MultiwfnJobSpec("igmh", fchk, {"fragment1": "1-2", "fragment2": ""}))
    assert not result.ok
    assert "两个非空片段" in result.error


def test_fake_multiwfn_esp_job_produces_validated_outputs(tmp_path):
    cube = """cube\ncreated by test\n    1 0.0 0.0 0.0\n    1 1.0 0.0 0.0\n    1 0.0 1.0 0.0\n    1 0.0 0.0 1.0\n    1 0.0 0.0 0.0 0.0\n 0.0\n"""
    script = tmp_path / "fake_multiwfn.py"
    script.write_text(
        "from pathlib import Path\n"
        f"cube={cube!r}\n"
        "Path('density.cub').write_text(cube)\n"
        "Path('totesp.cub').write_text(cube)\n"
        "print('Progress: 1 / 1')\n",
        encoding="utf-8",
    )
    fchk = tmp_path / "sample.fchk"; fchk.write_text("placeholder", encoding="ascii")
    settings = ToolSettings(sys.executable, tmp_path, tmp_path / "temp", tmp_path / "figures")
    service = FakeMultiwfnService(settings, script, ["density.cub", "totesp.cub"])
    result = service.run(MultiwfnJobSpec("esp", fchk))
    assert result.ok, result.error
    assert len(result.output_files) == 2
    assert all(path.is_file() for path in result.output_files)
    assert result.work_dir is not None and not result.work_dir.exists()


def test_fake_multiwfn_job_can_be_cancelled(tmp_path):
    script = tmp_path / "slow_multiwfn.py"
    script.write_text("import time\ntime.sleep(10)\n", encoding="utf-8")
    fchk = tmp_path / "sample.fchk"; fchk.write_text("placeholder", encoding="ascii")
    settings = ToolSettings(sys.executable, tmp_path, tmp_path / "temp", tmp_path / "figures")
    service = FakeMultiwfnService(settings, script, ["density.cub", "totesp.cub"])
    started = time.monotonic()
    result = service.run(MultiwfnJobSpec("esp", fchk), cancel=lambda: time.monotonic() - started > 0.35)
    assert not result.ok
    assert "取消" in result.error
