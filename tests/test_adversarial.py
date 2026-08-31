from pathlib import Path

from agent_flight_recorder.extract import build_trace
from agent_flight_recorder.parse import parse_turns
from agent_flight_recorder.pipeline import ingest_transcript


def _trace(text: str):
    return build_trace(parse_turns(text), text, source_path="memory")


def test_andrew_instruction_is_not_agent_refusal():
    trace = _trace("Andrew: Do not reset the repository.\nAgent: Okay.")
    assert trace.anti_patterns_avoided == []
    assert all(c.provenance[0].role != "human" for c in trace.anti_patterns_avoided)


def test_user_do_not_reset_agent_okay_is_not_refusal():
    trace = _trace("Human: Do not reset anything.\nAgent: Okay.")
    assert trace.anti_patterns_avoided == []


def test_historical_user_failure_is_not_current_failure():
    trace = _trace(
        "User: Yesterday the build failed with a dirty repo.\nAgent: Starting from a clean inspection."
    )
    assert trace.failures_recoveries == []


def test_word_freeze_in_docs_is_not_mutation_freeze():
    trace = _trace('Agent: The word "freeze" appears in the documentation.')
    assert all(event.phase != "freeze" for event in trace.observable_process)
    assert "AFR-P001" not in {p.pattern_id for p in trace.patterns_extracted}


def test_unrelated_4812_does_not_match_p006():
    trace = _trace("Agent: The invoice total is 4,812 dollars and is unrelated to shipping.")
    ids = {p.pattern_id for p in trace.patterns_extracted}
    assert "AFR-P006" not in ids


def test_repeated_weak_keyword_does_not_become_high_library_confidence(tmp_path):
    from agent_flight_recorder.library import empty_library, merge_trace

    weak = "Agent: The documentation mentions an environment and a project folder name.\n"
    library = empty_library(include_seed=True)
    for i in range(5):
        trace = _trace(weak)
        merge_trace(library, trace, session_id=f"weak-{i}")
    record = library.by_id()["AFR-P001"]
    # No real cue pair, so the pattern should not even attach.
    assert "weak-0" not in record.evidence_sessions
    assert record.confidence != "high"


def test_tool_error_then_user_advice_is_not_agent_recovery():
    text = (
        "Tool: error: compile failed with exit 1\n"
        "User: You should reset the repo and try again.\n"
        "Agent: I am going to read the compiler log instead."
    )
    # Next turn after the tool error is the user. That is not an observed agent recovery
    # for that pairing even if a later agent turn exists.
    trace = _trace(text)
    assert trace.failures_recoveries
    item = trace.failures_recoveries[0]
    assert item.failure_source_role == "tool"
    assert item.recovery_observed is False
    assert item.recovery_status == "unresolved"
    assert item.recovery_action is None


def test_andrew_diagnosis_is_not_agent_diagnosis():
    trace = _trace("Andrew: I think the root cause is X.\nAgent: I will inspect the logs.")
    diagnoses = [e for e in trace.observable_process if e.phase == "diagnose"]
    assert diagnoses == []
    assert all(e.provenance[0].role != "human" for e in trace.observable_process)


def test_positive_hypothesis_revise_verify_is_captured():
    text = (
        "Agent: Working theory: the parser is dropping trailing spaces.\n"
        "Tool: Checking fixtures/original.csv exists=true\n"
        "Agent: Evidence is against that hypothesis because raw values already preserve spaces.\n"
        "Agent: Revising the plan rather than changing the parser strip path.\n"
        "Agent: Tests pass after the scoped compare change. Verified checksum of the fixture."
    )
    trace = _trace(text)
    phases = [e.phase for e in trace.observable_process]
    assert "hypothesize" in phases
    assert "revise" in phases
    assert "verify" in phases
    assert all(event.provenance for event in trace.observable_process)


def test_sample_still_extracts_core_policies():
    sample = Path(__file__).resolve().parents[1] / "examples" / "broken_widget" / "transcript.md"
    trace = ingest_transcript(sample)
    ids = {p.pattern_id for p in trace.patterns_extracted}
    assert "AFR-P001" in ids
    assert "freeze" in [e.phase for e in trace.observable_process]
    assert any(c.provenance[0].role != "human" for c in trace.anti_patterns_avoided)
