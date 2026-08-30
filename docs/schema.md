# Trace shape

```
SESSION
  agent / model / date / project

GOAL
  what was being attempted

OBSERVABLE PROCESS
  inspect | hypothesize | execute | observe | diagnose | revise | verify | freeze | escalate

DECISION POINTS
  evidence that changed the plan

FAILURES / RECOVERIES
  what failed, what the agent did next

ANTI-PATTERNS AVOIDED
  destructive or unjustified actions it refused

PATTERNS EXTRACTED
  reusable operating behaviors with stable IDs when known

CONFIDENCE
  evidence strength

PROVENANCE
  exact transcript excerpts supporting each claim
```

JSON emitted by `afr ingest -o trace.json` follows this shape. See `schemas/trace.schema.json`.
