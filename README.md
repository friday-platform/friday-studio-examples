# Friday Studio Examples

[![Validate](https://github.com/friday-platform/friday-studio-examples/actions/workflows/validate.yml/badge.svg)](https://github.com/friday-platform/friday-studio-examples/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Ready-to-import workspace examples for [Friday Studio](https://hellofriday.ai) — the macOS app that runs AI workflows on your machine, on your schedule, with your data.

Each example is a complete workspace you can read end-to-end: a single `workspace.yml` describing what triggers the work, which agents do it, and how they fit together; a `workspace.lock` pinning versions; a README explaining setup; and screenshots of it running. Browse the folders directly — every example is meant to be readable as source.

> **What's a workspace?** A YAML file that bundles three things: **signals** (what starts the work — a schedule, an incoming message, a manual trigger), **agents** (what does the work — built-in agents for Gmail, GitHub, web research, and more, plus custom LLM agents), and **jobs** (how agents chain together into a sequence). Friday Studio reads the file, wires everything up, and runs it locally on your Mac. See the [docs](https://docs.hellofriday.ai) for the full picture.

## Examples

| Example | What it does |
|---|---|
| [GitHub Digest](github-digest) | Twice-weekly digest of your open PRs and review requests, no dashboard required |
| [Inbox Zero](inbox-zero) | Interactive Gmail triage — archive / keep / unread / delete decisions one email at a time |
| [Daily Operating Memo](daily-operating-memo) | Pulls today's calendar and priority email each morning and emails you a one-page daily plan |
| [Networking CRM](networking-crm) | Lightweight contact relationship tracking with reminders and follow-up nudges, driven by Telegram |
| [Competitive Monitor](competitive-monitor) | Weekly competitor intelligence brief — product, pricing, GTM, partnerships, leadership signals with sourced links |
| [GitHub PR Reviewer](github-pr-reviewer) | On-demand AI review of any GitHub pull request, posted back as a PR comment |
| [Google Sheets Query](google-sheets-query) | Natural-language Q&A over a Google Sheet |
| [RTX Price Monitor](rtx-price-monitor) | Hourly GPU price scraper that emails you when an RTX 5080 drops under your threshold |
| [DnD Campaign Manager](dnd-campaign-manager) | Persistent campaign state for tabletop RPG sessions — NPCs, locations, plot threads tracked across sessions |

> **First time?** Start with [GitHub Digest](github-digest) — one credential, runs on a schedule, digest lands in your workspace twice a week.

## Getting started

You'll need:

- A Mac (macOS 12 or later)
- [Friday Studio](https://hellofriday.ai) installed
- An [Anthropic API key](https://console.anthropic.com) — this is what powers the AI

### Run an example

The fastest path is straight from the app — no clone needed:

1. Open Friday Studio and click **Discover Spaces** in the sidebar.
2. Find the example you want and click **Add Space**. Friday imports it and opens its dashboard.
3. Connect any credentials the workspace needs (the per-example README lists them — usually one OAuth flow or an API token).
4. Trigger the workspace. Most examples run on a schedule, but you can also fire them manually from the **Run now** button or by chatting in the space.

Prefer to read the source first? Clone the repo and open any folder:

```sh
git clone https://github.com/friday-platform/friday-studio-examples.git
cd friday-studio-examples/github-digest
$EDITOR workspace.yml README.md
```

You can then point Friday at the local folder via **Add Space → From folder** if you want to run an edited copy. See the [Friday quickstart](https://docs.hellofriday.ai/getting-started/quickstart) for the full walkthrough.

### Write your own

1. Read [CONTRIBUTING.md](CONTRIBUTING.md) for the example template, naming conventions, and PR checklist.
2. Copy the closest existing example as a starting point.
3. Edit the `workspace.yml`, drop screenshots in `assets/<name>/`, register in `examples.json`, and open a PR.

If you'd rather have Friday build it for you, open the **Personal → Chat** tab in the app and describe what you want. Friday creates the workspace, picks the agents, and wires up the schedule through conversation.

## Repository layout

```text
.
├── <example-name>/
│   ├── workspace.yml      # signals, agents, jobs, memory, integrations
│   ├── workspace.lock     # pinned versions for reproducible imports
│   └── README.md          # what it does, setup, screenshots
├── assets/<example-name>/ # screenshots referenced by per-example READMEs
├── examples.json          # registry powering Discover Spaces inside Friday
└── .github/workflows/     # CI: validates structure, builds downloadable zips
```

Every example follows the same shape: a single `workspace.yml`, a `README.md`, and a folder under `assets/` with screenshots. The `examples.json` registry lists every example shipped in the in-app Discover Spaces library — adding a new example means adding a folder, a README, screenshots, and an entry in `examples.json`.

## Contributing

We welcome new examples and improvements. See [CONTRIBUTING.md](CONTRIBUTING.md) for the example template, naming conventions, and PR checklist. For security issues, see [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE) — use these examples as a starting point for your own workspaces.

## Links

- **Friday Studio** — [hellofriday.ai](https://hellofriday.ai)
- **Documentation** — [docs.hellofriday.ai](https://docs.hellofriday.ai)
- **Issues & feature requests** — [github.com/friday-platform/friday-studio-examples/issues](https://github.com/friday-platform/friday-studio-examples/issues)
