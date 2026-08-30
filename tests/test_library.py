from pathlib import Path

from agent_flight_recorder.library import empty_library
from agent_flight_recorder.pipeline import ingest_transcript, merge_into_library

ROOT = Path(__file__).resolve().parents[1] / "examples" / "broken_widget"


def test_library_accumulates_two_sessions():
    traces = [
        ingest_transcript(ROOT / "transcript.md"),
        ingest_transcript(ROOT / "transcript_second_session.md"),
    ]
    library = merge_into_library(traces)
    by_id = library.by_id()
    assert "AFR-P001" in by_id
    assert len(by_id["AFR-P001"].evidence_sessions) >= 2
    models = set(by_id["AFR-P001"].models_observed)
    assert "sample-codex" in models or "Codex" in models
    assert "sample-grok" in models or "Grok" in models


def test_seed_library_has_stable_ids():
    library = empty_library()
    ids = {p.pattern_id for p in library.patterns}
    assert ids == {f"AFR-P00{i}" for i in range(1, 7)}
