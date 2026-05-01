<!--
Thanks for the PR! A few notes before you submit:

- For a new example, please open or link a "Propose a new example" issue first if it isn't trivial.
- Run `python3 scripts/validate_examples.py` locally to catch structural issues.
- Screenshots must use synthetic / non-real data — no real personal data, real customer names, or production hostnames.
-->

## Summary

<!-- One paragraph: what does this PR change and why? -->

## Type of change

- [ ] New example workspace
- [ ] Improvement to an existing example (prompt, setup, screenshots, structure)
- [ ] Bug fix (broken FSM, dead signal input, wrong cron, broken link)
- [ ] Documentation only (README, CONTRIBUTING, SECURITY)
- [ ] Repo infra (CI, lint config, templates)

## Affected example(s)

<!-- e.g. `github-digest`, or `repo-wide` for cross-cutting changes -->

## Screenshots

<!--
For new examples or visual changes, paste screenshots of the workspace running.
Place files under `assets/<example-name>/` and reference them from the README.
-->

## Checklist

- [ ] I ran `python3 scripts/validate_examples.py` locally and it passed.
- [ ] If I added or renamed an example, I updated `examples.json` accordingly.
- [ ] If I added screenshots, they live under `assets/<example-name>/` and use synthetic / non-real data.
- [ ] No tokens, OAuth secrets, real emails, or internal hostnames appear in any committed file.
- [ ] The example follows the README structure described in [CONTRIBUTING.md](../blob/main/CONTRIBUTING.md) (Setup → What it looks like → How to use it → How it works → Notes).
- [ ] Folder name and `examples.json` `folder` are kebab-case and match exactly.
