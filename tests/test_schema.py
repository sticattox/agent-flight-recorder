from pathlib import Path

from agent_flight_recorder.pipeline import ingest_transcript
from agent_flight_recorder.schema import load_schema, validate_trace_dict

SAMPLE = Path(__file__).resolve().parents[1] / "examples" / "broken_widget" / "transcript.md"


def test_sample_trace_matches_schema():
    schema = load_schema()
    assert schema["required"] == ["schema_version", "session", "goal"]
    trace = ingest_transcript(SAMPLE)
    errors = validate_trace_dict(trace.to_dict())
    assert errors == []


def test_invalid_phase_is_rejected():
    errors = validate_trace_dict(
        {
            "schema_version": "0.2.1",
            "session": {},
            "goal": "x",
            "observable_process": [{"phase": "vibes", "summary": "nope"}],
        }
    )
    assert any("phase" in e for e in errors)
