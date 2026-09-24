# Cortex Data Pack — ingest this into your agent (Module 4)

This is a **refreshed pull** of Cortex's data — the week-of-`2026-07-06` snapshot.
Compared with the fixtures that shipped in your template, it has:

- **New engineering activity** for Northstar and Vega (merged PRs #820/#823/#442, a
  still-open Sev-1 #440, an open PR #448).
- **A moved metric:** Northstar activation `41% → 43%` week-over-week.
- **A brand-new confidential item:** `Pulsar` joins `Orbit` on the embargoed list.
- **Newer past updates + a new decision** reflecting all of the above.

In Module 4 you don't just *read* about grounding — you **ingest new data into your
own repo, run the agent on it, and push it to GitHub.** That's the loop every PM runs
when a data source updates.

---

## What's in this pack

Five files — the exact five that Cortex's tools read. Drop them into your repo's
`00-build/fixtures/`, replacing the older versions:

| File | Cortex tool that reads it |
|---|---|
| `projects.json` | `get_project`, `get_activity` |
| `past-updates.json` | `search_past_updates` |
| `decision-log.json` | `search_past_updates` |
| `roadmap.md` | `get_roadmap` |
| `team-norms.md` | `get_norms` |

> **Leave `task-happy.md`, `task-missing-data.md`, `task-jailbreak.md` alone** — those
> are the inbound tasks, not data sources. This pack does not include them.

---

## Ingest it (download → add → run → push)

From your forked `pm-os-agent` repo, open a terminal at the repo root:

```bash
# 1. Download cortex-data-pack.zip from the Module 4 resources, then unzip it
#    (double-click the zip, or: unzip ~/Downloads/cortex-data-pack.zip -d ~/Downloads/)

# 2. Copy the five data files into your fixtures (this overwrites the older pull)
cp ~/Downloads/cortex-data-pack/projects.json \
   ~/Downloads/cortex-data-pack/past-updates.json \
   ~/Downloads/cortex-data-pack/decision-log.json \
   ~/Downloads/cortex-data-pack/roadmap.md \
   ~/Downloads/cortex-data-pack/team-norms.md \
   00-build/fixtures/

# 3. See exactly what changed — this is the ingest, made visible
git status
git diff --stat

# 4. Run Cortex on the freshly-ingested data
cd 00-build && python agent.py && cd ..
#   Watch the draft cite the NEW numbers: activation 43% (prior 41%), PR #820/#823.
#   Withhold a source to prove grounding: python agent.py missing-data

# 5. Add it to your local repo, commit, and push to GitHub
git add 00-build/fixtures/
git commit -m "Ingest week-of-2026-07-06 data pack into Cortex fixtures"
git push
```

> On macOS use `python3` if `python` isn't found. Not comfortable in the terminal?
> Ask your coding agent: *"Copy the five files from `~/Downloads/cortex-data-pack/`
> into `00-build/fixtures/`, show me the diff, run `python agent.py`, then commit and
> push."*

---

## Prove the ingest worked

- ✅ `git diff --stat` shows the five fixture files changed.
- ✅ The run cites **43%** (not 41%) and the new PR numbers — Cortex is grounded on
  data *you* added.
- ✅ Withholding a source still makes Cortex **refuse or escalate** instead of
  inventing — `Pulsar` and `Orbit` never appear in a company-wide update.
- ✅ Your push shows the commit on GitHub.

That grounded run (and the withheld-source refusal) is exactly the two-state
screenshot Module 4's lab asks you to capture into `06-autonomy/prototype.md`.

---

## Want to go further? Use your *own* data instead

This pack is real-ish mock data so everyone has something to ingest. If you'd rather
ground Cortex in your **actual** team's norms, roadmap, and updates, follow
`00-build/fixtures/BRING-YOUR-OWN-DATA.md` — same ingest + push workflow, your numbers.
Keep the three teaching flags it lists (one confidential item, one held launch, one
citable metric) so the grounding probe still has something to catch.
