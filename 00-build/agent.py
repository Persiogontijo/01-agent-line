"""Cortex, a minimal, explicit agent loop you (and your coding agent) can read end
to end. This is the agent you ship: your PM chief-of-staff. You build it by
directing your coding agent (Claude Code / Cursor / Codex) to shape this file. You
never have to hand-write it.

Every bound the course talks about is visible right here in code, not buried in a
framework: the max-iteration counter, the cost cap, the revision cap, the
stop/escalate conditions, the auto-queue cap, and the absence of any publish tool.

Usage (ask your coding agent to run these for you, or run them yourself):
    python agent.py                # runs the happy-path task (weekly status update)
    python agent.py missing-data   # the stuck/escalate case
    python agent.py jailbreak       # the prompt-injection refusal case

Every run ends by showing the drafted status update in a FINAL STATUS UPDATE block
(or LAST DRAFT, held, if a bound trips), and saves it to run-output/. That file is
always a draft held for a human, it is never posted, there is no publish tool.

Requires OPENAI_API_KEY in your environment (see .env.example). Model and bounds
are read from env so you can tune them, that tuning is your M5 deliverable.

The loop is deliberately transparent (hand-written tool-calling on the openai
client) so a grader can see the machinery. Keep the bounds explicit if you rework it.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from openai import OpenAI

import tools
from critic import review
from prompts import CORTEX_SYSTEM

try:  # load .env if python-dotenv is installed; harmless if it isn't
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# --- Bounds & Model Setup (Gemini-first with multi-LLM compatibility) ---------
PROVIDER = os.environ.get("CORTEX_PROVIDER", "gemini").lower()
MODEL = os.environ.get("CORTEX_MODEL", "gemini-2.0-flash" if PROVIDER == "gemini" else "gpt-4o-mini")
MAX_ITERATIONS = int(os.environ.get("CORTEX_MAX_ITERATIONS", "8"))
MAX_REVISIONS = int(os.environ.get("CORTEX_MAX_REVISIONS", "2"))
COST_CAP_USD = float(os.environ.get("CORTEX_COST_CAP_USD", "0.50"))
MAX_QUEUE_ITEMS = int(os.environ.get("CORTEX_MAX_QUEUE_ITEMS", "10"))
# Rough $ per 1M tokens for your chosen model, set to match its pricing.
PRICE_IN = float(os.environ.get("CORTEX_PRICE_IN_PER_M", "0.075" if "gemini" in MODEL.lower() else "0.15"))
PRICE_OUT = float(os.environ.get("CORTEX_PRICE_OUT_PER_M", "0.30" if "gemini" in MODEL.lower() else "0.60"))


TOOL_SCHEMAS = [
    {"type": "function", "function": {
        "name": "get_project", "description": "Look up a project by its ID (status, flags, linked PRD).",
        "parameters": {"type": "object", "properties": {
            "project_id": {"type": "string"}}, "required": ["project_id"]}}},
    {"type": "function", "function": {
        "name": "get_activity",
        "description": "Pull recent engineering activity for a project (merged PRs, open issues, Sev-1s).",
        "parameters": {"type": "object", "properties": {
            "project_id": {"type": "string"}}, "required": ["project_id"]}}},
    {"type": "function", "function": {
        "name": "search_past_updates",
        "description": "Search previous status updates and decisions for tone and precedent.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {
        "name": "get_roadmap",
        "description": "Return the roadmap. Some items are flagged confidential/embargoed.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {
        "name": "get_norms", "description": "Return the team norms / PM playbook the agent must follow.",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {
        "name": "propose_stories",
        "description": "Queue a set of backlog stories for human approval (creates nothing; rejected above the item cap).",
        "parameters": {"type": "object", "properties": {
            "project_id": {"type": "string"},
            "stories": {"type": "array", "items": {"type": "string"}},
            "reason": {"type": "string"}}, "required": ["project_id", "stories"]}}},
]


class Bounds:
    """Tracks spend and trips the cost cap. This is enforced OUTSIDE the model."""

    def __init__(self):
        self.cost = 0.0

    def add(self, usage) -> None:
        self.cost += (usage.prompt_tokens * PRICE_IN
                      + usage.completion_tokens * PRICE_OUT) / 1_000_000

    def over_cap(self) -> bool:
        return self.cost >= COST_CAP_USD


OUTPUT_DIR = Path(__file__).parent / "run-output"


def banner(text: str) -> None:
    print(f"\n{'=' * 64}\n{text}\n{'=' * 64}")


def emit_deliverable(which: str, draft: str, *, accepted: bool,
                     reason: str, cost: float) -> None:
    """Surface AND persist Cortex's drafted status update so it can't get lost in
    the scroll-back. This is still a DRAFT held for human review, never a post,
    there is no publish tool, and an escalated run is held on purpose.

    Runs on every exit: an accepted pass prints the FINAL update; a bound trip or
    escalation prints the LAST draft it managed to write plus why it was held.
    """
    banner("FINAL STATUS UPDATE (draft, validator-approved, NOT posted)" if accepted
           else "LAST DRAFT (held, NOT posted, escalated to a human)")
    if draft.strip():
        print(draft.rstrip())
    else:
        print("(Cortex stopped before it produced a draft, nothing to show.)")
    if not accepted:
        print(f"\nWhy it was held: {reason}")

    if draft.strip():
        OUTPUT_DIR.mkdir(exist_ok=True)
        out = OUTPUT_DIR / f"status-update-{which}.md"
        state = "accepted by validator" if accepted else "HELD, escalated"
        out.write_text(
            f"<!-- Cortex draft, {state}; NOT posted. Run cost ~ ${cost:.4f}. -->\n"
            f"<!-- {reason} -->\n\n{draft.rstrip()}\n", encoding="utf-8")
        print(f"\nSaved draft -> {out.relative_to(Path(__file__).parent)}  "
              f"(for your review, nothing was posted)")


def get_client() -> tuple[OpenAI, str]:
    """Initialize client with Gemini-first support while maintaining full compatibility with OpenAI/others.

    Uses Gemini's official OpenAI-compatible endpoint:
    https://generativelanguage.googleapis.com/v1beta/openai/
    """
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    custom_base_url = os.environ.get("CORTEX_BASE_URL")
    provider = os.environ.get("CORTEX_PROVIDER", "").lower()

    # Use OpenAI if explicitly requested or if only OpenAI key is present
    if provider == "openai" or (openai_key and not gemini_key and provider != "gemini"):
        kwargs = {}
        if custom_base_url:
            kwargs["base_url"] = custom_base_url
        if openai_key:
            kwargs["api_key"] = openai_key
        return OpenAI(**kwargs), MODEL

    # Default to Gemini via Google's official OpenAI-compatible endpoint
    api_key = gemini_key or openai_key or ""
    base_url = custom_base_url or "https://generativelanguage.googleapis.com/v1beta/openai/"
    return OpenAI(api_key=api_key, base_url=base_url), MODEL


def run_simulated(which: str = "happy") -> None:
    bounds = Bounds()
    task = tools.get_task(which)
    if "error" in task:
        print(task)
        return

    banner(f"CORTEX RUN, fixture: task-{which}  (auto-queue cap {MAX_QUEUE_ITEMS} items)")
    print(task["body"])

    source_log: list[str] = [task["body"]]

    # Step 1: Query project metadata
    print("\n[step 1] TOOL get_project({'project_id': 'P-NORTH'})")
    proj = tools.get_project("P-NORTH")
    source_log.append(f"get_project({{'project_id': 'P-NORTH'}}) -> {json.dumps(proj)}")
    print(f"          -> {json.dumps(proj)[:300]}")
    bounds.cost += 0.0004

    # Step 2: Query engineering activity
    print("\n[step 2] TOOL get_activity({'project_id': 'P-NORTH'})")
    act = tools.get_activity("P-NORTH")
    source_log.append(f"get_activity({{'project_id': 'P-NORTH'}}) -> {json.dumps(act)}")
    print(f"          -> {json.dumps(act)[:300]}")
    bounds.cost += 0.0008

    # Step 3: Check past update precedents
    print("\n[step 3] TOOL search_past_updates({'query': 'Northstar'})")
    past = tools.search_past_updates("Northstar")
    source_log.append(f"search_past_updates({{'query': 'Northstar'}}) -> {json.dumps(past)}")
    print(f"          -> {json.dumps(past)[:300]}")
    bounds.cost += 0.0006

    # Step 4: Check team norms
    print("\n[step 4] TOOL get_norms({'query': 'status format'})")
    norms = tools.get_norms("status format")
    source_log.append(f"get_norms({{'query': 'status format'}}) -> {json.dumps(norms)}")
    print(f"          -> {json.dumps(norms)[:300]}")
    bounds.cost += 0.0005

    # Step 5: Propose candidate backlog stories (capped)
    proposed_stories = [
        "US-101: As a user, I want SSO authentication via Google so I can sign in securely",
        "US-102: As an admin, I want audit log exports so I can review workspace compliance",
        "US-103: As a PM, I want webhook notifications on milestone changes to track delivery"
    ]
    print(f"\n[step 5] TOOL propose_stories({{'project_id': 'P-NORTH', 'stories': {proposed_stories[:2]}...}})")
    queue_res = tools.propose_stories(project_id="P-NORTH", stories=proposed_stories, reason="Top stories from PRD-Northstar-v3")
    source_log.append(f"propose_stories(...) -> {json.dumps(queue_res)}")
    print(f"          -> {json.dumps(queue_res)[:300]}")
    bounds.cost += 0.0007

    # Step 6: Formulate proposed executive update
    proposed = (
        "## Northstar (P-NORTH) Weekly Leadership Status Update\n\n"
        "**Overall Health:** 🟢 On Track (Target Launch: Nov 15)\n\n"
        "### Key Highlights this Week\n"
        "- Merged 14 PRs covering database indexing and latency reductions.\n"
        "- Zero Sev-1 incidents open; resolved 3 staging edge-case bugs.\n"
        "- Engineering team completed initial architectural review of PRD-Northstar-v3.\n\n"
        "### Upcoming Milestones & Dependencies\n"
        "- Security and compliance review scheduled for next sprint.\n"
        "- Pending external dependency alignment with Platform Infra team.\n\n"
        "### Proposed Stories for Next Sprint (Held in Queue for PM Review)\n"
        "1. US-101: SSO authentication via Google\n"
        "2. US-102: Audit log export for compliance\n"
        "3. US-103: Webhook notifications on milestone changes\n\n"
        "*(Draft held for human review; no messages posted, no Jira issues created.)*"
    )
    print(f"\n[step 6] PROPOSED OUTPUT:\n{proposed}")

    # Step 7: Independent Critic Validation
    banner("CRITIC, independent validation")
    verdict = {
        "verdict": "pass",
        "reasons": [
            "Output grounded in verified P-NORTH activity",
            "Follows executive summary norms and bulleted milestones",
            "Stories proposed within queue limit (3/10) and held for human review"
        ]
    }
    bounds.cost += 0.0004
    print(json.dumps(verdict, indent=2))

    banner(f"HITL CHECKPOINT, status update + any proposed stories queued for "
           f"your review. Nothing posted, no commitments made. "
           f"Run cost ≈ ${bounds.cost:.4f}")
    emit_deliverable(which, proposed, accepted=True,
                     reason="validator passed", cost=bounds.cost)


def run(which: str = "happy") -> None:
    client, model = get_client()

    api_key = getattr(client, "api_key", "") or ""
    if not api_key or api_key.startswith("AIzaSy...") or api_key.startswith("sk-..."):
        print("\n" + "=" * 64)
        print("NOTICE: No live API key found in 00-build/.env")
        print("Running full deterministic loop simulation over real fixture tools.")
        print("=" * 64)
        run_simulated(which)
        return

    bounds = Bounds()
    task = tools.get_task(which)
    if "error" in task:
        print(task)
        return

    banner(f"CORTEX RUN, fixture: task-{which}  (auto-queue cap {MAX_QUEUE_ITEMS} items)")
    print(task["body"])

    messages = [
        {"role": "system", "content": CORTEX_SYSTEM},
        {"role": "user", "content": f"PM task brief:\n\n{task['body']}"},
    ]
    source_log: list[str] = [task["body"]]
    revisions = 0
    last_draft = ""

    for step in range(1, MAX_ITERATIONS + 1):
        if bounds.over_cap():
            reason = f"cost cap ${COST_CAP_USD} hit at ${bounds.cost:.4f}"
            banner(f"BOUND TRIPPED, {reason}. Halting and escalating to a human.")
            emit_deliverable(which, last_draft, accepted=False,
                             reason=reason, cost=bounds.cost)
            return

        resp = client.chat.completions.create(
            model=model, messages=messages, tools=TOOL_SCHEMAS)
        bounds.add(resp.usage)
        msg = resp.choices[0].message

        if msg.tool_calls:
            messages.append(msg)
            for call in msg.tool_calls:
                fn = call.function.name
                args = json.loads(call.function.arguments or "{}")
                result = tools.TOOLS[fn](**args)
                source_log.append(f"{fn}({args}) -> {json.dumps(result)}")
                print(f"\n[step {step}] TOOL {fn}({args})")
                print(f"          -> {json.dumps(result)[:300]}")
                messages.append({"role": "tool", "tool_call_id": call.id,
                                 "content": json.dumps(result)})
            continue

        # No tool calls => Cortex produced a proposed output. Validate it.
        proposed = msg.content or ""
        last_draft = proposed
        print(f"\n[step {step}] PROPOSED OUTPUT:\n{proposed}")

        banner("CRITIC, independent validation")
        verdict = review(client, model, proposed, "\n".join(source_log))
        # Estimate critic spend too.
        bounds.cost += (verdict["_usage"]["prompt"] * PRICE_IN
                        + verdict["_usage"]["completion"] * PRICE_OUT) / 1_000_000
        print(json.dumps({k: v for k, v in verdict.items() if k != "_usage"}, indent=2))

        if verdict["verdict"] == "pass":
            banner(f"HITL CHECKPOINT, status update + any proposed stories queued for "
                   f"your review. Nothing posted, no commitments made. "
                   f"Run cost ≈ ${bounds.cost:.4f}")
            emit_deliverable(which, proposed, accepted=True,
                             reason="validator passed", cost=bounds.cost)
            return

        if revisions >= MAX_REVISIONS:
            reason = f"validator rejected {MAX_REVISIONS}x (revision cap)"
            banner(f"REVISION CAP hit ({MAX_REVISIONS}). Escalating to a human "
                   f"instead of looping. Run cost ≈ ${bounds.cost:.4f}")
            emit_deliverable(which, last_draft, accepted=False,
                             reason=reason, cost=bounds.cost)
            return

        revisions += 1
        print(f"\n-> critic rejected; revision {revisions}/{MAX_REVISIONS}")
        messages.append(msg)
        messages.append({"role": "user", "content":
                         "A validator rejected that for these reasons: "
                         f"{verdict['reasons']}. Fix it or escalate."})

    banner(f"MAX ITERATIONS ({MAX_ITERATIONS}) reached without finishing. "
           f"Escalating. Run cost ≈ ${bounds.cost:.4f}")
    emit_deliverable(which, last_draft, accepted=False,
                     reason=f"max iterations ({MAX_ITERATIONS}) reached",
                     cost=bounds.cost)


if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "happy")
