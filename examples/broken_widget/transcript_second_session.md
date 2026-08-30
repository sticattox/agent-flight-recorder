agent: Grok
model: sample-grok
date: 2026-08-30
project: widget-cli
goal: Repair the test runner after the source move.

User: Tests are launching from the old build folder. Fix that, don't wreck the specimen.

Agent: The test command still assumes ~/Projects/widget-cli-v2-build is the repo. That assumption is now uncertain.

Status: Read-only until the governing boundary is known. No edits, no cleanup, no resets.

Tool: Same tests against candidate roots: old build folder, installed v1, dedicated source, snapshot.

Agent: Confirmed: pytest config in the old build folder still points at itself. Dedicated source is the live tree. Snapshot exists. Task-owned state is one pytest.ini and two test files copied by habit into the specimen.

Agent: I will not clean ~/Projects to "see better." I will not edit the specimen. Bounded target is pytest.ini in the dedicated source only.

Agent: Because the specimen must stay untouched, I copied nothing back from it. I wrote pytest.ini in dedicated source instead. Tests pass from that repository.
