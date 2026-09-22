# Prototype: Cortex PM Chief-of-Staff Agent

> Module 6 · ★ Deliverable 1, the working agent demo
>
> ✅ **What this validates:** the agent actually runs end to end, by the end you'll have proven it with real screenshots of your Cortex across the six required moments (M2 to M6).

## What it does

_One paragraph: the agent in action, end to end._

## How you built it

- **Coding agent:** _which one you directed (Claude Code / Cursor / Codex)_
- **Model + bounds:** _model used, max iterations, cost cap, queue cap_
- **Repo / config:** _path to your build in `00-build/`_
- **Live link:** _[shareable URL, optional bonus]_

## Screenshots (required, collected M2 to M6)

Real screenshots of *your* Cortex running. These are the `00-build/CORTEX-ANATOMY.md` set and they are required, a link alone is not enough.

| # | Screenshot | What it shows | From |
|---|---|---|---|
| 1 | _[img]_ | happy-path run: a real drafted update + the HITL checkpoint (queued, not posted) | M2 |
| 2 | See trace below | the critic rejecting a bad draft (revise/block) | M3 |
| 3 | _[img]_ | a grounded update citing pulled activity + a caught hallucination | M4 |
| 4 | _[img]_ | jailbreak refused + escalated | M5 |
| 5 | _[img]_ | an iteration/cost/queue bound halting a runaway | M5 |
| 6 | _[img]_ | end-to-end run | M6 |

### M3 Capture: Critic Rejecting a Bad Draft
*Caption: Independent validator critic catches an ungrounded metric ('99.9% query latency reduction') and unauthorized date commitment ('Firm GA: Oct 1st'), rejecting the draft and triggering revision 1/2 before passing on revision.*

```text
================================================================
CRITIC, independent validation (Pass 1)
================================================================
{
  "verdict": "fail",
  "reasons": [
    "Check 1 (Factual Grounding) FAILED: Claim of '99.9% query latency reduction' is an invented metric not found in get_activity data.",
    "Check 3 (No Unauthorized Commitments) FAILED: Committed to firm GA launch date 'Oct 1st' without leadership approval, violating team norms."
  ]
}

-> critic rejected; revision 1/2

[step 7] RE-DRAFTING: Cortex removes ungrounded 99.9% latency claim and retracts firm GA date commitment based on critic feedback...

[step 8] PROPOSED OUTPUT (Revision 1):
## Northstar (P-NORTH) Weekly Leadership Status Update

**Overall Health:** 🟡 Needs Alignment (Target Launch: Nov 15, pending platform alignment)
...
================================================================
CRITIC, independent validation (Pass 2)
================================================================
{
  "verdict": "pass",
  "reasons": [
    "Check 1 (Factual Grounding) PASSED: All metrics match verified P-NORTH activity.",
    "Check 3 (No Unauthorized Commitments) PASSED: Firm GA date retracted; status adheres to team norms."
  ]
}
```

## How to run it

_Minimal steps for someone to reproduce the demo (env vars, and the command or the coding-agent prompt you used)._
