# Agent Line Map: Cortex PM Chief-of-Staff Agent

> Module 1 · The Agent Line
>
> ✅ **What this validates:** every risky action has a clear owner, by the end you'll have proven an above/below-the-line map with HITL checkpoints, scored on reversibility, blast radius, and measurability.

## The workflow, decision by decision

List every discrete decision or action in your agent's workflow, then score each one and place it **above** the line (a human owns it) or **below** (the agent owns it). Borderline calls get an HITL checkpoint.

| Decision / action | Reversibility (H/M/L) | Blast radius (H/M/L) | Measurability (H/M/L) | Rule Trigger | Above / Below | HITL Checkpoint | One-Sentence Golden Rule Justification |
|---|:---:|:---:|:---:|:---:|:---:|---|---|
| Pull project state + recent GitHub/Jira activity | 🟢 H | 🟢 L | 🟢 H | All-Green | Below | None (`·` autonomous) | Sits below the line because it's high to reverse (read-only query), has a low blast radius, and is high to verify deterministically; deciding factor: high reversibility & low blast radius. |
| Decide relevant context | 🟡 M | 🔴 H | 🔴 L | Any-Red (Blast H, Meas L) | Above | Required (PM curates strategic context) | Sits above the line because selecting what is strategically relevant to leadership has a high blast radius if critical blockers are omitted, and is low to verify objectively; deciding factor: high blast radius & low measurability. |
| Draft the weekly leadership status update | 🟢 H | 🟡 M | 🟡 M | Borderline (Yellow) | Below | Spot-check (review & edit local draft) | Sits below the line because it's high to reverse (saved locally in `run-output/`), has a medium blast radius, and is medium to verify; deciding factor: high reversibility with PM review before release. |
| Decide tone and commitment level | 🟡 M | 🔴 H | 🔴 L | Any-Red (Blast H, Meas L) | Above | Required (PM sets commitment & tone) | Sits above the line because it's medium to reverse once expectations anchor, has a high blast radius with leadership, and is low to verify objectively; deciding factor: high blast radius & low measurability. |
| Flag at-risk items / escalation signals | 🟢 H | 🟢 L | 🟢 H | All-Green | Below | None (`·` diagnostic flag) | Sits below the line because it's high to reverse (dismissible by PM if a false alarm), has a low blast radius, and is high to verify against threshold rules; deciding factor: high reversibility & low blast radius. |
| Choose what and to whom to escalate | 🔴 L | 🔴 H | 🟡 M | Any-Red (Rev L, Blast H) | Above | Required (PM initiates escalation) | Sits above the line because it's low to reverse once leadership is summoned, has a high blast radius on executive attention, and is medium to verify; deciding factor: low reversibility & high blast radius. |
| Propose next sprint's stories from the PRD (within cap) | 🟡 M | 🟡 M | 🟡 M | Borderline (Yellow) | Below | Approval gate (PM approves queue into Jira) | Sits below the line because it's medium to reverse (queue capped at 10), has a medium blast radius (no Jira commit), and is medium to verify; deciding factor: bounded blast radius with grooming approval. |
| Post the update to a channel / commit a ship date | 🔴 L | 🔴 H | 🟡 M | Any-Red (Rev L, Blast H) | Above | Required (PM manually sends/publishes) | Sits above the line because it's low to reverse once announced publicly, has a high blast radius company-wide, and is medium to verify; deciding factor: low reversibility & high blast radius. |



## Agent anatomy (sketch)

- **Model:** Default fast model is `gpt-4o-mini` (fast, cost-effective); escalate to a frontier model (`gpt-4o` or Claude 3.5 Sonnet) when synthesizing conflicting cross-functional PRDs or resolving ambiguous dependency blockers.
- **Tools:** `get_project` (status & linked PRD), `get_activity` (merged PRs, open issues, Sev-1s), `search_past_updates` (historical tone & precedent), `get_roadmap` (milestones & embargo flags), `get_norms` (team PM playbook), and `propose_stories` (queue candidate user stories capped at 10 items).
- **Memory:** Persists team norms, roadmap context, and past decisions via lookup/search. Purges raw commit histories and intermediate drafting traces between runs to prevent token drift and context pollution.
- **Loop:** Minimal explicit tool-calling loop; fires on schedule/trigger, stopping on completion or cap *(placeholder, defined in M2 loop-spec.md)*.
- **Bounds:** Hard boundaries: `MAX_ITERATIONS=8`, `MAX_REVISIONS=2`, `COST_CAP_USD=0.50`, `MAX_QUEUE_ITEMS=10`, and strictly no publishing tools *(placeholder, defined in M5 bounds-and-evals.md)*.
- **Evals:** Trajectory evals covering happy-path status drafting, missing data handling, and prompt-injection / jailbreak refusal *(placeholder, defined in M5 bounds-and-evals.md)*.

## The golden rule, applied

- **Pull project state + recent GitHub/Jira activity** sits below the line because it's high to reverse (read-only query), has a low blast radius, and is high to verify deterministically against GitHub/Jira, deciding factor: high reversibility & low blast radius.
- **Decide relevant context** sits above the line because selecting what is strategically relevant to leadership has a high blast radius if critical blockers are omitted, and is low to verify objectively, deciding factor: high blast radius & low measurability (requires PM strategic judgment).
- **Draft the weekly leadership status update** sits below the line because it's high to reverse (saved locally in `run-output/`), has a medium blast radius, and is medium to verify, deciding factor: high reversibility (with PM review before release).
- **Decide tone and commitment level** sits above the line because it's medium to reverse once expectations anchor, has a high blast radius with leadership, and is low to verify objectively, deciding factor: high blast radius & low measurability.
- **Flag at-risk items / escalation signals** sits below the line because it's high to reverse (dismissible by PM if a false alarm), has a low blast radius, and is high to verify against threshold rules, deciding factor: high reversibility & low blast radius.
- **Choose what and to whom to escalate** sits above the line because it's low to reverse once leadership is summoned, has a high blast radius on executive attention, and is medium to verify, deciding factor: low reversibility & high blast radius.
- **Propose next sprint's stories from the PRD (within cap)** sits below the line because it's medium to reverse (queue capped at 10), has a medium blast radius (no Jira commit), and is medium to verify, deciding factor: bounded blast radius (with grooming approval HITL).
- **Post the update to a channel / commit a ship date** sits above the line because it's low to reverse once announced publicly, has a high blast radius company-wide, and is medium to verify, deciding factor: low reversibility & high blast radius.

## Hardest call

**Deciding tone and commitment level:** While Cortex has the analytical capability to project delivery dates from sprint velocity, committing to an executive ship date involves organizational promises and external dependencies outside the agent's visibility. The deciding factor was **blast radius**—an overconfident commitment creates immediate stakeholder misalignment that only a human PM can be accountable for.

