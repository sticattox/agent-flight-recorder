from pathlib import Path

from agent_flight_recorder.cli import main

SAMPLE = Path(__file__).resolve().parents[1] / "examples" / "broken_widget" / "transcript.md"


def test_cli_ingest_print(tmp_path, capsys):
    out = tmp_path / "trace.json"
    code = main(["ingest", str(SAMPLE), "-o", str(out), "--print"])
    assert code == 0
    printed = capsys.readouterr().out
    assert "SESSION" in printed
    assert "GOAL" in printed
    assert out.exists()
    assert "observable_process" in out.read_text(encoding="utf-8")


def test_cli_render_roundtrip(tmp_path, capsys):
    out = tmp_path / "trace.json"
    assert main(["ingest", str(SAMPLE), "-o", str(out)]) == 0
    capsys.readouterr()
    assert main(["render", str(out)]) == 0
    printed = capsys.readouterr().out
    assert "SESSION" in printed
    assert "PATTERNS EXTRACTED" in printed


def test_cli_library(tmp_path, capsys):
    lib = tmp_path / "lib.json"
    second = SAMPLE.parent / "transcript_second_session.md"
    code = main(["library", str(SAMPLE), str(second), "-o", str(lib), "--print"])
    assert code == 0
    printed = capsys.readouterr().out
    assert "AFR-P001" in printed
    assert lib.exists()
