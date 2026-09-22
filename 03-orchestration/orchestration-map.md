# Orchestration Map: Cortex PM Chief-of-Staff Agent

> Module 3 · Orchestration & Subagents, ★ Deliverable 3
>
> ✅ **What this validates:** nothing advances unchecked, by the end you'll have proven a justified topology, a roster, and a validator with a defined fail action.
>
> Builds on your M2 Loop Spec. Only split one agent into a team when there's a real reason, coordination has a cost.

## 1. Why split? (or why not)

**Decision:** Split with a single independent validator subagent (the critic).

**Rationale (Learner's words):**
> *"Split with a critic, it gives us more quality on reports, and keep system not too complex, and also is not so costly."*

**The 4-factor split evaluation:**
- **Separation of concerns (No):** Single primary loop handles data retrieval and initial draft synthesis without role confusion.
- **Parallelism (No):** Tool calls run quickly in sequence; a multi-agent gathering fleet would add unnecessary token and latency overhead.
- **Independent validator (Yes):** A drafter cannot reliably evaluate its own hallucinations or omissions. An isolated critic subagent validates factual grounding and norms compliance without inheriting the drafter's context blind spots.
- **Context-window pressure (No):** Ingested project and sprint fixture payloads remain well within the model's context budget.

## 2. Topology

**Pattern:** `Single + Subagents`

```
[Trigger: Pre-Meeting Hook / Cron]
              │
              ▼
[Cortex (Chief-of-Staff)] ──(reads tools: project, activity, norms)──► drafts update + stories
              │
              ▼
    [Critic Subagent] (Isolated Gemini call)
        │         │
 (pass) │         │ (fail, up to 2 revisions)
        │         └───────────────┐
        ▼                         ▼
[PM Review Gate]           [Cortex re-drafts]
 (held in run-output/)            │
                                  ▼ (if fails > 2 times)
                           [Escalate to PM]
```

## 3. Roster

| Agent / subagent | Responsibility | Runs which Loop Spec |
|---|---|---|
| **Cortex (Chief-of-Staff)** | Orchestrates retrieval, synthesizes status update & queues candidate backlog stories | M2 loop (`agent.py`) |
| **Critic (Validator)** | Independent evaluation of draft against source data, confidentiality, and norms | M3 critic loop (`critic.py`) |
| **Human PM** | Final approval and release gate; reviews held draft in `run-output/` | HITL Gate (M1 Agent Line) |

## 4. Communication & hand-offs

- **Protocol:** Synchronous in-process Python call (`review(client, model, proposed_output, source_data)`).
- **Hand-off payload:**
  - *Input to Critic:* `source_data` (string containing project metadata, engineering activity, roadmap, and norms) + `proposed_output` (Cortex's draft).
  - *Output from Critic:* Strict JSON: `{"verdict": "pass" | "fail", "reasons": ["..."]}`.
- **Delivery:** Drafts passing review are saved locally to `run-output/status-update-<task>.md` for human review; no external messaging or ticket-publishing API is ever called.

## 5. The validator

- **What the critic checks:**
  1. **Factual Grounding (Anti-hallucination):** Every metric, progress claim, blocker, and PR/issue ID must be directly traceable to pulled source data (`get_project`, `get_activity`, `get_roadmap`); zero invented figures or unbacked status calls.
  2. **Confidentiality Guard:** Zero leakage of confidential or embargoed roadmap items into broader/external status updates.
  3. **No Unauthorized Commitments:** Tone respects team norms; no unconfirmed delivery dates, promises, or launch gates committed that Cortex cannot authorize.
  4. **Queue Cap Enforcement:** Proposed backlog stories must not exceed `MAX_QUEUE_ITEMS = 10` candidate stories.
  5. **No Auto-Publish / Tool Restraint:** Output must remain strictly a local draft held for human review (`run-output/`); zero attempts to auto-merge PRs, create/close Jira tickets, or post publicly.
- **Fail action:** **Revise, then escalate.** The critic returns `{"verdict": "fail", "reasons": [...]}` back to Cortex for re-drafting. If still failing after reaching the revision cap, Cortex halts and transfers ownership to the human PM at the HITL gate.
- **Revision cap:** **Max 2 revisions (`MAX_REVISIONS = 2`).** Prevents infinite critic loops and limits latency/token spend.
- **Pass action:** When `{"verdict": "pass"}`, the draft advances to the PM review checkpoint in `run-output/status-update-<task>.md` (zero auto-send).

## 6. State: shared vs isolated

- **Shared State:**
  - The raw pulled source data (`source_data`) representing project state, activity, roadmap, and team norms.
  - The drafted update text (`proposed_output`).
- **Isolated State:**
  - **Cortex's internal scratchpad & history:** Cortex's tool-call history, internal chain-of-thought, and prompt context remain completely hidden from the critic to avoid contaminating the evaluation or inheriting drafter blind spots.
  - **Critic's system instructions & reasoning:** The critic evaluates independently; Cortex only receives the structured verdict and the list of `reasons` for revision.
  - **Harness execution bounds:** Iteration counts and the revision cap (`MAX_REVISIONS = 2`) are tracked externally in `agent.py` rather than within model memory.

## 7. Cost & latency budget

- **Model Calls Overhead:**
  - Happy-path (immediate pass): **+1 model call** for critic review.
  - Worst-case (capped at `MAX_REVISIONS = 2`): **+5 model calls** (2 re-drafts + 3 critic evaluations) before escalating to the PM.
- **Latency Impact (Gemini 2.0 Flash):**
  - Happy-path: **+0.5s – 1.0s** overhead before the draft reaches the PM checkpoint.
  - Worst-case: **+3s – 5s** total before human hand-off.
- **Token Spend & Financial Bound:**
  - Happy-path: ~1,500 input + 100 output tokens (~**$0.0002** per run).
  - Worst-case: ~7,500 cumulative tokens (~**$0.002** total), safely below the `COST_CAP_USD = $0.50` limit enforced in `agent.py` (forward-linked to M5 bounds).
