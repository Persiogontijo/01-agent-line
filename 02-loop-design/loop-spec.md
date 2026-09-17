# Loop Spec: Cortex PM Chief-of-Staff Agent

> Module 2 · Loop Engineering, ★ Deliverable 2
>
> ✅ **What this validates:** the agent knows when to run and when to stop, by the end you'll have proven a one-page Loop Spec with a trigger, a definition of "done," and explicit stop conditions.
>
> Your one-page blueprint for how the work you handed to the agent (M1) actually *runs*.
> An agent is just a prompt that fires itself, this spec says when it fires, what "done" means, and what it needs to do the job. Living document; refine as the course progresses.

## 1. Trigger & loop type

**Chosen type:** **Hook with Cron Backup (Hybrid)**

- **Primary Trigger (Pre-Meeting Hook):** Calendar Event Hook that monitors the PM's schedule and fires **30 minutes prior** to recurring high-stakes meetings (e.g., *"Agentic Workflows & Loops"* or weekly Leadership Review). Dispatches an interactive confirmation modal and begins execution only after the PM grants approval.
- **Secondary Trigger (Weekly Cadence Cron):** Scheduled Cron sweep running every **Monday at 9:00 AM (`0 9 * * 1`)** to assemble weekly project velocity and status if no meeting hook was triggered earlier.
- **On-Demand Trigger (Artifact Hook):** Activates when a new or updated PRD is detected (`PRD-Northstar-v3`) to propose candidate backlog stories ahead of sprint planning.
- **Ruled-Out Types:** 
  - *Heartbeat* was ruled out because continuous polling without event anchors produces redundant queries and burns tokens.
  - Pure *Goal Loop* was ruled out because executive reporting requires strict temporal grounding tied to business cadences.
- **Idempotency & Deduplication:** Runs are keyed by `event_id + event_date` (calendar) or `sprint_id + week_number` (cron). If triggered multiple times within the same window, Cortex detects the existing draft in `run-output/` and halts to avoid duplicate updates.

## 2. Goal / definition of done

*"Done means Cortex has ingested project state (`P-NORTH`) and recent engineering activity (PRs, issues, Sev-1s), drafted a leadership status update grounded in team norms, queued up to 10 candidate sprint backlog stories from the PRD, passed independent critic validation, and saved the final draft locally in `run-output/status-update-<task>.md` for human review—with zero public messages posted and no Jira tickets modified."*

## 3. Stop conditions

| Condition | What it looks like | What happens |
|---|---|---|
| **Success** | Draft assembled, stories $\le 10$, and Independent Critic returns `{"verdict": "pass"}`. | Emits draft to `run-output/status-update-<task>.md`, halts at HITL checkpoint, logs run cost, and alerts PM for review. |
| **Stuck / give up** | Project ID not found in registry, or engineering activity query fails/returns empty after retry. | Halts execution immediately, logs deterministic error (`"project_not_found"`), and escalates missing data alert to PM without looping. |
| **Escalate to human** | 1. **Critic Revision Cap:** Critic rejects 2 consecutive revisions (`MAX_REVISIONS = 2`).<br>2. **Cost Cap:** Token spend reaches $0.50 (`COST_CAP_USD = 0.50`).<br>3. **Iteration Cap:** Loop reaches 8 steps (`MAX_ITERATIONS = 8`).<br>4. **Queue Overflow:** Story proposals exceed cap (`MAX_QUEUE_ITEMS = 10`).<br>5. **Adversarial Injection:** Untrusted issue/PR text attempts to bypass norms or auto-publish. | Halts loop, retains `LAST DRAFT (held)`, logs explicit failure reason, and transfers decision ownership to the human PM at the HITL gate. |

## 4. State

- **Persistent State (Cross-run):** Team norms playbook (`team-norms.md`), roadmap milestones (`roadmap.md`), historical status precedents (`past-updates.json`), and calendar schedule mapping (`calendar_sync.py`). Accessible via read-only tools.
- **Transient State (Purged per run):** In-memory conversation context, raw GitHub/Jira commit payloads, and intermediate revision attempts are strictly cleared between runs to avoid token leakage, memory bloat, and cross-project confidentiality breaches.

## 5. The five things a loop can lean on

| Component | For Cortex |
|---|---|
| **Work tree** (isolated workspace per run, a git worktree) | Uses isolated local execution in `00-build/`; deliverables saved to git-ignored `run-output/` so incomplete runs never pollute source control. |
| **Skills** (reusable capabilities) | System prompts in `prompts.py` defining role personas (`CORTEX_SYSTEM`), executive briefing conventions, and INVEST story criteria. |
| **Plugins / connectors** (tools & access, optional if you don't have one yet) | Native macOS Calendar bridge (`calendar_sync.py`) detecting calendar appointments; mock Jira/GitHub data connectors (`tools.py`). |
| **Subagents** (independent check when the loop can't grade itself) | Independent Critic Validator (`critic.py` with `CRITIC_SYSTEM`) running in a separate, isolated context to evaluate factual grounding before human hand-off *(formalized in M3)*. |
| **State tracking** | In-code `Bounds` object tracking token cost, iteration count, and cumulative `source_log` audit trail for each step. |

## Link to live loop

- [`00-build/agent.py`](../00-build/agent.py)
