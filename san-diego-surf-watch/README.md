# San Diego Surf Watch

A surf conditions monitor for San Diego area beaches. Every 30 minutes, it checks wave height, period, wind, and swell direction across 9 beaches from Ocean Beach to Oceanside, evaluates whether conditions are worth paddling out, and saves an alert to memory when they are.

It covers:

- **Wave height** — filtered to 3 feet or larger
- **Wave period** — 8 seconds or longer for clean, organized swell
- **Wind** — offshore or light (under 10 mph); flags choppy onshore wind above 15 mph as poor
- **Swell direction** — NW, W, or SW (optimal for San Diego's south-facing beaches)

Good conditions trigger a `SURF ALERT` entry in long-term memory. Poor conditions log a one-liner to notes and move on.

---

## Setup

### 1. Download Friday

1. Go to [hellofriday.ai](https://hellofriday.ai) and download the macOS installer
2. Open the DMG and drag Friday to your Applications folder
3. Launch Friday and complete the initial setup

### 2. Import the workspace

1. Open Friday and go to **Discover Spaces**
2. Find this workspace and click it
3. Click **Add Space**

### 3. That's it

No credentials required. The workspace uses a web agent to check public surf forecast sites (Surfline, Magic Seaweed, and similar). No API key, no OAuth flow.

---

## What a surf alert looks like

When conditions meet the threshold, the evaluator writes to memory:

> **SURF ALERT:** Swamis (Encinitas) — 4–5 ft, 12 sec period, light NW wind, W swell. Clean lines, waist-to-head high. Worth paddling out before 10am.

Poor conditions log a note instead:

> Surf check 07:30: conditions poor — 1–2 ft wind swell, 13 mph onshore SW wind.

---

## How to use it

It runs automatically every 30 minutes. Nothing to trigger, nothing to open.

To check conditions on demand, open the workspace chat and ask Friday what the surf looks like. The evaluator has all prior check results in memory and can answer without running a new web search.

---

## How it works

| Component | Role |
|---|---|
| `surf-checker` | Atlas web agent — searches Surfline, Magic Seaweed, and similar sites for current conditions at 9 San Diego area beaches |
| `surf-evaluator` | LLM agent (Claude Sonnet) — applies good/poor criteria, decides whether to alert, writes one memory entry |
| `surf-watch` job | Sequential two-agent execution: checker runs first, evaluator runs on its output |
| `surf-check-cron` signal | Schedule signal firing every 30 minutes (`*/30 * * * *`) |

The cron fires `surf-watch`, which runs `surf-checker` then `surf-evaluator` in sequence. The checker returns structured conditions for all beaches. The evaluator applies the criteria, picks the best beach if conditions qualify, and writes exactly one memory entry — a `SURF ALERT` to `memory` (long-term) if good, or a brief note to `notes` (short-term) if not.

---

## Notes

- Beaches covered: Ocean Beach, Mission Beach, Pacific Beach, La Jolla Shores, Del Mar, Solana Beach, Swamis (Encinitas), Carlsbad, Oceanside.
- The evaluator is instructed to write exactly one memory entry per run — no flooding your memory store with 48 identical poor-condition entries per day.
- The workspace is configured for David Woolf in San Diego. To change the persona or the good-surf thresholds, edit the `surf-evaluator` prompt in `workspace.yml`.
- The cron runs on UTC. Adjust the `timezone` field in `workspace.yml` under `signals.surf-check-cron.config` if you want the schedule expressed in local time.
- All data stays within your Friday workspace and public surf forecast sites. No external services beyond the LLM call and web search.
