from pathlib import Path

from agent_flight_recorder.pipeline import ingest_transcript

SAMPLE = Path(__file__).resolve().parents[1] / "examples" / "broken_widget" / "transcript.md"


def test_sample_has_goal_and_freeze():
    trace = ingest_transcript(SAMPLE)
    assert "json" in trace.goal.lower()
    phases = [e.phase for e in trace.observable_process]
    assert "freeze" in phases
    assert "diagnose" in phases
    assert "inspect" in phases


def test_refusals_are_cited():
    trace = ingest_transcript(SAMPLE)
    text = " ".join(c.statement.lower() for c in trace.anti_patterns_avoided)
    assert "clean" in text or "reset" in text or "no edits" in text
    assert all(c.provenance for c in trace.anti_patterns_avoided)


def test_seed_patterns_attach():
    trace = ingest_transcript(SAMPLE)
    ids = {p.pattern_id for p in trace.patterns_extracted}
    assert "AFR-P001" in ids
    assert "AFR-P002" in ids


def test_every_process_event_has_excerpt():
    trace = ingest_transcript(SAMPLE)
    assert trace.observable_process
    assert all(event.provenance and event.provenance[0].excerpt for event in trace.observable_process)


def test_session_meta_from_header():
    trace = ingest_transcript(SAMPLE)
    assert trace.session.agent == "Codex"
    assert trace.session.project == "widget-cli"


def test_confidence_high_is_reachable_when_goal_is_known():
    from agent_flight_recorder.extract import confidence_for
    from agent_flight_recorder.models import Claim, FlightTrace, ProcessEvent, Provenance

    cited = [
        ProcessEvent(
            phase="inspect",
            summary=f"step {i}",
            provenance=[Provenance(excerpt=f"excerpt {i}")],
        )
        for i in range(8)
    ]
    extra = [Claim(statement="refused reset", provenance=[Provenance(excerpt="no reset")])]
    trace = FlightTrace(goal="Add --json", observable_process=cited, anti_patterns_avoided=extra)
    assert confidence_for(trace)["strength"] == "high"


def test_ingest_existing_trace_json_keeps_process(tmp_path):
    original = ingest_transcript(SAMPLE)
    path = tmp_path / "trace.json"
    path.write_text(__import__("json").dumps(original.to_dict()), encoding="utf-8")
    loaded = ingest_transcript(path)
    assert loaded.goal == original.goal
    assert [e.phase for e in loaded.observable_process] == [e.phase for e in original.observable_process]
    assert len(loaded.anti_patterns_avoided) == len(original.anti_patterns_avoided)
    assert loaded.session.project == original.session.project
