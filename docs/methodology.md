# Methodology

Agent Flight Recorder captures **visible** process, not hidden chain-of-thought.

A session is useful when you can point at status notes, tool output, refusals, and plan changes. A session is not useful when the only signal is fluent prose.

## What to capture

- Goal the user actually stated
- Inspections and their results
- Hypotheses that were tested
- Evidence that changed the plan
- Failures and the next action
- Actions the agent refused
- Operating patterns that could fire again
- Verbatim excerpts for each claim

## What not to capture

- Hidden reasoning the product does not show
- Private product internals from some other repository
- Secrets, home-directory dumps, credentials
- Prose style to imitate

## Resume gate

Do not treat a session as ready to mutate an environment, and do not praise an agent for "moving on," unless all five are known:

1. Governing boundary
2. Task-owned state, quantified
3. Trusted baseline
4. Preservation artifact
5. Bounded mutation target

If any field is unknown, the correct recorded move is freeze or escalate.

## Symmetric probe

Generate candidate explanations. Run the same discriminating tests on each. Compare. Then rank.

Applies to Git roots, processes, ports, config files, models, services, dependency versions, and duplicate installs.

## Policy excludes

Compare a task tree to a trusted baseline with

`exclude = runtime_or_user_owned_paths_from_project_policy`

Do not bake another project's folder names into the general rule.

## Research question

Can weaker local agents improve by extracting observable operating policies from stronger agents, rather than by imitating their prose?

This repository exists to make that question testable.
