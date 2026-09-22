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

### Visual Orchestration Flow

```mermaid
flowchart TD
    %% Triggers
    subgraph Triggers ["⚡ Trigger Layer"]
        T1["Pre-Meeting Hook<br/>(Calendar Event: 30 min before)"]
        T2["Weekly Cron<br/>(Monday 9:00 AM)"]
        T3["On-Demand PRD Hook<br/>(PRD-Northstar-v3 update)"]
    end

    %% Cortex Orchestrator
    subgraph PrimaryAgent ["🤖 Primary Agent: Cortex (Chief-of-Staff)"]
        direction TB
        C1["Ingest PM Task Brief & Context"]
        C2["Execute Tool Calls in Sequence"]
        C3["Synthesize Draft Update & Queue Stories"]
    end

    %% Tool Ecosystem
    subgraph Tools ["🛠️ Tool & Fixture Boundary (Read-Only + Propose)"]
        direction TB
        TL1["get_project('P-NORTH')"]
        TL2["get_activity('P-NORTH')"]
        TL3["search_past_updates('Northstar')"]
        TL4["get_norms('status format')"]
        TL5["propose_stories(queue <= 10)"]
    end

    %% State Isolation Boundary
    subgraph StateBoundary ["🔒 State Isolation Boundary"]
        SB["Hand-off Payload Only:<br/>• source_data (raw facts)<br/>• proposed_output (draft text)<br/>(Cortex scratchpad & internal thoughts are HIDDEN)"]
    end

    %% Independent Validator Subagent
    subgraph CriticSubagent ["🛡️ Independent Validator Subagent (Critic)"]
        CR1["Load Independent Gemini Context<br/>(System Prompt: CRITIC_SYSTEM)"]
        CR2{"Validate 5 Checkable Rules:<br/>1. Factual Grounding<br/>2. Confidentiality Guard<br/>3. No Unauthorized Dates<br/>4. Queue Cap <= 10<br/>5. No Auto-Publish"}
    end

    %% Revision and Escalation Logic
    subgraph ControlFlow ["⚙️ Harness Control & Bounds (agent.py)"]
        REV{"Revisions < 2?"}
        ESC["🚨 ESCALATE to Human PM<br/>(Revision cap hit / Bounds tripped)"]
    end

    %% Human Review Gate
    subgraph HITL ["👤 Human-in-the-Loop Gate (Above the Agent Line)"]
        HOLD["Save Draft Locally<br/>run-output/status-update-task.md"]
        PM["PM Reviews, Approves, & Releases<br/>(Zero auto-send / No publish tool)"]
    end

    %% Flow Connections
    T1 --> C1
    T2 --> C1
    T3 --> C1

    C1 --> C2
    C2 <--> TL1
    C2 <--> TL2
    C2 <--> TL3
    C2 <--> TL4
    C2 <--> TL5
    C2 --> C3

    C3 --> SB
    SB --> CR1
    CR1 --> CR2

    %% Critic Verdicts
    CR2 -- "verdict: pass" --> HOLD
    CR2 -- "verdict: fail" --> REV

    REV -- "Yes (Rev 1/2)" -->|Return failure reasons| C3
    REV -- "No (Cap Hit)" --> ESC
    ESC --> PM
    HOLD --> PM

    %% Styling
    classDef trigger fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;
    classDef agent fill:#ede7f6,stroke:#512da8,stroke-width:2px;
    classDef tool fill:#fbe9e7,stroke:#d84315,stroke-width:2px;
    classDef critic fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef hitl fill:#fff3e0,stroke:#ef6c00,stroke-width:2px;
    classDef control fill:#fce4ec,stroke:#c2185b,stroke-width:2px;

    class T1,T2,T3 trigger;
    class C1,C2,C3 agent;
    class TL1,TL2,TL3,TL4,TL5 tool;
    class CR1,CR2 critic;
    class HOLD,PM hitl;
    class REV,ESC,SB control;
```

### Key Architectural Characteristics

| Architectural Step / Layer | Pattern / Mechanism | Concrete Behavior in Cortex | Enforcement & Safety Boundary |
|---|---|---|---|
| **1. Trigger Layer** *(Starts the Loop)* | **Hybrid: Event Hook with Cron Backup** | **Three Triggers:**<br>• **Primary:** Calendar Hook fires **30 mins before** weekly leadership/status meetings.<br>• **Secondary (Backup):** Cron sweep every **Monday at 9:00 AM** (`0 9 * * 1`).<br>• **On-Demand:** Artifact hook fires when a PRD update is detected (`PRD-Northstar-v3`). | **Idempotency & Deduplication:** Runs are keyed by `event_id + date` or `sprint_id + week`. If a draft exists in `run-output/`, the loop halts to prevent duplicate queries or token burn. |
| **2. Topology** | **Single + Validator Subagent** | Cortex acts as the primary drafter/orchestrator; an independent critic subagent evaluates the output prior to human delivery. | Subagent operates strictly as a read-only inspector; no lateral agent-to-agent tool calls or unconstrained agent sprawl. |
| **3. State Boundary** | **Strict Context Isolation** | Cortex only passes `source_data` (raw facts) and `proposed_output` (draft). Scratchpad, tool reasoning, and chain-of-thought are hidden from the critic. | Prevents drafter confirmation bias and guarantees the critic cannot inherit drafting blind spots. |
| **4. Validator Checks** | **5 Deterministic Rules** | Inspects: (1) Factual Grounding, (2) Confidentiality / Embargoes, (3) Unauthorized Date Commitments, (4) Queue Cap ($\le 10$), (5) Tool Restraint. | Critic returns structured JSON `{"verdict": "pass" \| "fail", "reasons": [...]}`. Fails on *any* non-compliant rule. |
| **5. Feedback Loop** | **Tiered Fail-Action** | On failure, the critic bounces the draft back with explicit reasons (`revision 1/2`) so Cortex can self-correct ungrounded claims or commitments. | Bounded by `MAX_REVISIONS = 2`. If exceeded, execution halts immediately and escalates to human PM. |
| **6. Harness Bounds** | **External Circuit Breakers** | Spend cap (`COST_CAP_USD = $0.50`), loop limit (`MAX_ITERATIONS = 8`), and queue cap (`MAX_QUEUE_ITEMS = 10`) tracked outside model memory. | Hard-coded in `agent.py`; model instructions cannot override or negotiate these limits. |
| **7. The Agent Line** | **HITL Review Checkpoint** | Drafts are written locally to `run-output/status-update-<task>.md` for PM approval and release. | **Zero publishing tools.** Cortex possesses no API capability to post to Slack, create Jira tickets, or merge PRs. |

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
