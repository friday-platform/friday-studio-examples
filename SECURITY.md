# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in any of the workspace examples in this repository, please report it privately so we can address it before public disclosure.

**Please do not open a public GitHub issue for security reports.**

Email security reports to **security@hellofriday.ai** with:

- A description of the issue and the example(s) affected
- Steps to reproduce, or a proof of concept
- The impact you believe it has (data exposure, credential leakage, code execution, etc.)
- Any suggested remediation

You can expect an initial acknowledgement within 3 business days. We will keep you updated as we investigate and prepare a fix, and will credit you in the release notes once the fix ships, unless you prefer to remain anonymous.

## Scope

This repository contains example Friday workspaces (`workspace.yml` files, prompts, and supporting docs). In-scope reports include:

- Example workspaces that leak credentials, secrets, or user data
- Prompts or jobs that could be coerced into destructive behavior against connected accounts (Gmail, GitHub, Google Drive, etc.) by untrusted input
- MCP server configurations that grant excessive privileges by default
- Supply-chain concerns with how examples reference external resources

Vulnerabilities in the Friday desktop app itself, or in upstream MCP servers, should be reported to their respective maintainers. For Friday app issues, see [hellofriday.ai](https://hellofriday.ai).

## Using Examples Safely

These workspaces are starting points, not hardened production templates. When importing an example:

- Review the `workspace.yml` and any prompts before granting credentials
- Use scoped tokens (read-only where possible) rather than account-wide credentials
- Run examples that touch destructive actions (delete, send, post) in a test account first
