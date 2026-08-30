from agent_flight_recorder.parse import extract_metadata, parse_turns


def test_parse_speaker_turns():
    text = "User: do the thing\nAgent: I will inspect first\nStill agent.\n"
    turns = parse_turns(text)
    assert turns[0].speaker == "user"
    assert turns[1].speaker == "agent"
    assert "Still agent" in turns[1].text


def test_metadata_header():
    text = "agent: Codex\nproject: widget-cli\n\nUser: hi\n"
    meta = extract_metadata(text)
    assert meta["agent"] == "Codex"
    assert meta["project"] == "widget-cli"


def test_unlabeled_document_is_one_agent_turn():
    turns = parse_turns("just a blob of notes")
    assert len(turns) == 1
    assert turns[0].speaker == "agent"
