# Contributing

Thanks for considering a contribution. This repo collects example workspaces for [Friday](https://hellofriday.ai). The bar is "would a stranger discovering Friday find this useful and easy to import" — practical examples that work end-to-end, with clear setup instructions.

## Ways to contribute

- **Add a new example workspace** — a complete, end-to-end use case
- **Improve an existing example** — clearer prompts, better defaults, missing screenshots
- **Fix a bug** — broken FSM, dead signal input, wrong cron, broken link
- **Improve documentation** — typos, clearer setup steps, missing context

## Adding a new example

Every example must follow the same shape so the catalog stays browsable.

### 1. Create the folder

Use **kebab-case** for the folder name (e.g. `meeting-notes-summarizer`, not `meeting_notes_summarizer` or `MeetingNotesSummarizer`).

```
my-new-example/
├── workspace.yml
├── workspace.lock
└── README.md
assets/my-new-example/
└── screenshot-1.png
```

### 2. Write the workspace

`workspace.yml` should declare:

- `version: '1.0'` and a `workspace.name` / `workspace.description`
- Any `tools.mcp.servers` the example depends on
- `signals` — schedules, manual triggers, or external events
- `jobs` — the FSM tying signals to agents
- `agents` — LLM, atlas (web/calendar/etc.), or custom agents
- `memory` — `own` stores plus standard `mounts` for `user-notes` and `user-memory` (read-only)

A few conventions worth honoring:

- **Schedules:** prefer `timezone: America/Los_Angeles` unless there's a reason otherwise. Keep cron expressions in the workspace's local timezone, not UTC, so they don't drift across DST.
- **Email recipient placeholder:** use the literal string `"[ADD EMAIL RECIPIENT HERE]"` (quoted) so the YAML is unambiguous and the user knows what to replace.
- **Signal parameters:** if your signal accepts parameters (e.g. `competitors`, `lookback_days`), reference them in agent prompts via `{{ signal.data.<param> }}` rather than hardcoding values.
- **FSM:** every job's FSM should have an `idle` initial state, transitions on signal events, and a `done: { type: final }` terminal state.

Look at `github-digest/`, `daily-operating-memo/`, and `competitive-monitor/` for reference patterns.

### 3. Write the README

Per-example READMEs follow this structure:

```markdown
# Example Name

A one-paragraph description of what the workspace does and when it runs.

## Setup

### 1. Download Friday
(link to hellofriday.ai)

### 2. Import the workspace
(Discover Spaces flow)

### 3. Connect <integration>
(per-integration credential setup)

### 4. Configure (if needed)
(any placeholders to replace)

## What it looks like
(screenshot + example output)

## How to use it
(triggering, schedule, on-demand)

## How it works
(table of components: agents, jobs, signals, MCP servers)

## Notes
(timezone, customization tips, data handling)
```

### 4. Add screenshots

Place screenshots in `assets/<example-name>/`. Use real-looking but **non-real** data — never include actual personal data, internal company data, real customer names, or production hostnames in screenshots. Synthetic test data is fine; redact or regenerate anything sensitive.

### 5. Register in `examples.json`

Add an entry at the end of `examples.json`:

```json
{
  "name": "My New Example",
  "folder": "my-new-example"
}
```

The `name` is the human-readable title shown on the download site. The `folder` must match the directory name exactly. The deploy workflow will fail if a listed folder is missing.

### 6. Open a PR

Use the PR template. Include:

- A one-paragraph summary
- A screenshot or two of the example running
- Confirmation that no real personal data is in any committed asset

## Style and conventions

- **Folders:** kebab-case (`my-example`, not `my_example` or `MyExample`)
- **YAML:** use `>-` or `|-` block scalars for multi-line prompts; avoid escaped `\n` in single-line strings
- **Comments:** keep workspace.yml comments minimal — let descriptive names and the README do the explaining
- **Screenshots:** PNG, kept under ~1MB each; meaningful filenames (`pr-digest-output.png`, not `Screenshot 2024-...png`)

## Reporting issues

For bugs and feature requests, use the issue templates. For security concerns, see [SECURITY.md](SECURITY.md).

## Code of Conduct

By participating, you agree to abide by the [Code of Conduct](CODE_OF_CONDUCT.md).
