# Friday Studio Examples

[![Validate](https://github.com/friday-platform/friday-studio-examples/actions/workflows/validate.yml/badge.svg)](https://github.com/friday-platform/friday-studio-examples/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A collection of ready-to-import workspace examples for [Friday Studio](https://hellofriday.ai) — a macOS desktop app for building **agentic workspaces** that run on a schedule, react to signals, and stitch together LLMs, MCP servers, and your tools.

Each example is a complete workspace you can read end-to-end: a single `workspace.yml` declaring signals, jobs, agents, and memory; a `workspace.lock` pinning versions; a README explaining setup; and screenshots of it running. Browse the folders directly in this repo — every example is meant to be readable as source.

> **What is a Friday Studio workspace?** A YAML-defined unit that bundles one or more *signals* (cron schedules, HTTP triggers, calendar events), *jobs* (FSMs that run when a signal fires), *agents* (LLM, atlas web/calendar, or custom), *memory* stores, and *MCP servers* it talks to. The Friday desktop app imports a `workspace.yml`, materializes the agents, and runs them locally.

## Examples

| Example | What it does |
|---|---|
| [Competitive Monitor](competitive-monitor) | Weekly competitor intelligence brief — product, pricing, GTM, partnerships, leadership signals with sourced links |
| [Daily Operating Memo](daily-operating-memo) | Pulls today's calendar and priority email each morning and emails you a one-page daily plan |
| [DnD Campaign Manager](dnd-campaign-manager) | Persistent campaign state for tabletop RPG sessions — NPCs, locations, plot threads tracked across sessions |
| [GitHub Digest](github-digest) | Twice-weekly digest of your open PRs and review requests, no dashboard required |
| [GitHub PR Reviewer](github-pr-reviewer) | On-demand AI review of any GitHub pull request, posted back as a PR comment |
| [Google Sheets Query](google-sheets-query) | Natural-language Q&A over a Google Sheet via the Sheets MCP server |
| [Inbox Zero](inbox-zero) | Interactive Gmail triage — archive / keep / unread / delete decisions one email at a time |
| [Networking CRM](networking-crm) | Lightweight contact relationship tracking with reminders and follow-up nudges |
| [RTX Price Monitor](rtx-price-monitor) | Hourly GPU price scraper that emails you when an RTX 5080 drops under your threshold |

## Getting started

Pick the path that fits what you're here to do.

### Read the source

Every example is a single `workspace.yml` plus a README. Open one and read top to bottom — this is the fastest way to learn what a Friday workspace looks like and how to write your own.

```sh
git clone https://github.com/friday-platform/friday-studio-examples.git
cd friday-studio-examples/github-digest
$EDITOR workspace.yml README.md
```

Good starting points:

- [`github-digest/workspace.yml`](github-digest/workspace.yml) — minimal scheduled job with one LLM agent and one MCP server
- [`competitive-monitor/workspace.yml`](competitive-monitor/workspace.yml) — atlas web agent + multi-step research pipeline
- [`networking-crm/workspace.yml`](networking-crm/workspace.yml) — Telegram-driven interactive workspace with persistent memory

### Run an example locally

You'll need [Friday Studio](https://hellofriday.ai) installed (macOS).

1. Clone this repo: `git clone https://github.com/friday-platform/friday-studio-examples.git`
2. In Friday, choose **Import workspace from folder** and point it at one of the example directories (e.g. `friday-studio-examples/github-digest`).
3. Connect credentials when prompted (GitHub PAT, Google OAuth, etc.). The per-example README documents what's needed and which scopes.
4. Trigger the workspace — most examples have either a schedule, an HTTP signal, or a manual `run-now` button in the Friday UI.

If you'd rather skip the clone, the same examples are available inside Friday under **Discover Spaces** — click any example to import it directly.

### Write your own

1. Read [CONTRIBUTING.md](CONTRIBUTING.md) for the example template, naming conventions, and PR checklist.
2. Copy the closest existing example as a starting point.
3. Edit the `workspace.yml`, drop screenshots in `assets/<name>/`, register in `examples.json`, and open a PR.

## Repository layout

```text
.
├── <example-name>/
│   ├── workspace.yml      # signals, jobs, agents, memory, MCP servers
│   ├── workspace.lock     # pinned versions for reproducible imports
│   └── README.md          # what it does, setup, screenshots
├── assets/<example-name>/ # screenshots referenced by per-example READMEs
├── examples.json          # registry consumed by the GitHub Pages deploy
└── .github/workflows/     # CI: builds downloadable zips for each example
```

Every example follows the same shape: a single `workspace.yml`, a `README.md`, and a folder under `assets/` with screenshots. The `examples.json` registry lists every example shipped on the public download site — adding a new example means adding a folder, a README, screenshots, and an entry in `examples.json`.

## Contributing

We welcome new examples and improvements. See [CONTRIBUTING.md](CONTRIBUTING.md) for the example template, naming conventions, and PR checklist. For security issues, see [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE) — use these examples as a starting point for your own workspaces.

## Links

- **Friday product** — [hellofriday.ai](https://hellofriday.ai)
- **Documentation** — [docs.hellofriday.ai](https://docs.hellofriday.ai)
- **Issues & feature requests** — [github.com/friday-platform/friday-studio-examples/issues](https://github.com/friday-platform/friday-studio-examples/issues)
