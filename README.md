# Friday Studio Examples

[![Validate](https://github.com/friday-platform/friday-studio-examples/actions/workflows/validate.yml/badge.svg)](https://github.com/friday-platform/friday-studio-examples/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A collection of ready-to-import workspace examples for [Friday](https://hellofriday.ai) — a desktop platform for building agentic workspaces that run on a schedule, react to signals, and stitch together LLMs, MCP servers, and your tools.

Each example is a complete workspace: a `workspace.yml` describing signals, jobs, agents, and memory, plus a README explaining what it does, how to set it up, and what it looks like in action.

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

You don't need to clone this repo to use the examples. The fastest path is to import them from inside the Friday app.

1. **Install Friday.** Download the macOS installer from [hellofriday.ai](https://hellofriday.ai), drag to Applications, and complete the initial setup.
2. **Open Discover Spaces** in Friday. Browse the catalog, find the example you want, and click **Add Space**.
3. **Configure credentials.** Most examples need at least one connection (GitHub PAT, Google OAuth, etc.). The per-example README walks through what's needed.

If you'd rather work from a local checkout — e.g. to edit a workspace before importing, or to base a new workspace on an existing one — clone this repo, edit the `workspace.yml`, and import it via Friday's local-workspace import flow.

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
