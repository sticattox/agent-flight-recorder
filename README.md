# Agent Flight Recorder

Turn observable AI development sessions into structured, evidence-backed agent behavior traces.

You already watch capable coding agents inspect, freeze, diagnose, refuse unsafe cleanup, and only then resume. That work usually dies in a chat log. AFR turns the **visible** part of those sessions into records you can store, compare, and accumulate into a pattern library.

It does not scrape hidden chain-of-thought. It does not imitate prose. It records operating policy.

## Why this exists

The interesting question is not "can a small model sound like a strong agent."

The interesting question is:

> Can you improve weaker local agents by extracting observable operating policies from stronger agents, rather than trying to imitate their prose?

AFR is a tool for that question.

## Install

```bash
git clone https://github.com/sticattox/agent-flight-recorder.git
cd agent-flight-recorder
python -m pip install -e .
```

Python 3.11+. No required third-party dependencies.

## Quick start

```bash
afr ingest examples/broken_widget/transcript.md --print
afr ingest examples/broken_widget/transcript.md -o traces/widget.json
afr render traces/widget.json

afr library examples/broken_widget/transcript.md \
            examples/broken_widget/transcript_second_session.md \
            -o examples/library/widget-library.json --print
```

A record looks like this:

```
SESSION
  agent / model / date / project

GOAL
  what was being attempted

OBSERVABLE PROCESS
  inspect
  hypothesize
  execute
  observe
  diagnose
  revise
  verify

DECISION POINTS
  evidence that changed the plan

FAILURES / RECOVERIES
  what failed
  what the agent did next

ANTI-PATTERNS AVOIDED
  destructive or unjustified actions it refused

PATTERNS EXTRACTED
  reusable operating behaviors

CONFIDENCE
  evidence strength

PROVENANCE
  exact transcript excerpts supporting each claim
```

## Pattern library

One session can say "the agent stopped editing when the workspace looked wrong."

Several sessions should collapse into a stable policy:

**AFR-P001 — Reduce mutation authority when foundational assumptions become uncertain**

The library stores evidence counts, trigger conditions, recovery sequences, models observed, confidence, and excerpts pointing back at source traces.

Seed policies included:

| ID | Policy |
| --- | --- |
| AFR-P001 | Freeze writes when a foundational assumption looks false |
| AFR-P002 | Probe candidate explanations symmetrically |
| AFR-P003 | Stay diagnostic until the resume gate passes |
| AFR-P004 | Compare to a trusted baseline using project-policy excludes |
| AFR-P005 | Preserve partial work before repairing the environment |
| AFR-P006 | Do not clean dirt the current task does not own |

## Resume gate

Do not leave diagnostic / frozen mode until all of these are known:

- governing boundary
- task-owned state, quantified
- trusted baseline
- preservation artifact
- bounded mutation target

If any field is unknown: remain read-only or escalate.

## Public / private

This repo is the software, schemas, fabricated samples, and generic pattern definitions.

Keep real internal architecture, private chats, proprietary prompts, and lab machine paths out of it. See [docs/public-private-boundary.md](docs/public-private-boundary.md).

## Versions

- **v0.1** transcript → structured trace
- **v0.2** evidence-linked pattern extraction
- **v0.2.1** speaker-role normalization, role-aware failure pairing, separated confidence, adversarial negatives
- **v0.3** multi-session library + tighter dedup *(partial)*
- **v0.4** compare two agents on the same task *(not shipped)*
- later: export operating cards for local coding agents

v0.2.1 prefers omission over invention. Human instructions, historical anecdotes, and incidental tokens are not agent behavior.

## Tests

```bash
python -m pytest
```

## License

MIT
