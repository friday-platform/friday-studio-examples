#!/usr/bin/env python3
"""Structural validator for friday-studio-examples.

Checks:
  * examples.json is well-formed and every entry has a unique kebab-case folder + name
  * every registered folder exists with workspace.yml, workspace.lock, README.md
  * every example folder at the repo root is registered in examples.json
  * every example has an assets/<folder>/ directory with at least one PNG
  * each workspace.yml parses as YAML and declares the keys Friday needs:
      version, workspace.name, workspace.description, signals, jobs, agents
  * each job has an FSM with an `idle` initial state and a final state
  * any signal/job/agent referenced from a trigger or transition is defined

Exits non-zero with a list of problems for CI to surface.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SKIP_DIRS = {".github", ".claude", ".git", "assets", "site", "node_modules", "scripts"}


def discover_example_folders() -> list[str]:
    folders = []
    for entry in sorted(REPO_ROOT.iterdir()):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        if entry.name in SKIP_DIRS:
            continue
        folders.append(entry.name)
    return folders


def load_examples_json(errors: list[str]) -> list[dict]:
    path = REPO_ROOT / "examples.json"
    if not path.exists():
        errors.append("examples.json: missing at repo root")
        return []
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        errors.append(f"examples.json: invalid JSON ({exc})")
        return []
    if not isinstance(data, list):
        errors.append("examples.json: must be a JSON array")
        return []
    return data


def validate_examples_json(entries: list[dict], folders: list[str], errors: list[str]) -> None:
    seen_names: set[str] = set()
    seen_folders: set[str] = set()
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"examples.json[{i}]: must be an object")
            continue
        name = entry.get("name")
        folder = entry.get("folder")
        extra = set(entry) - {"name", "folder"}
        if not isinstance(name, str) or not name.strip():
            errors.append(f"examples.json[{i}]: missing or empty 'name'")
        elif name in seen_names:
            errors.append(f"examples.json[{i}]: duplicate name '{name}'")
        else:
            seen_names.add(name)
        if not isinstance(folder, str) or not folder.strip():
            errors.append(f"examples.json[{i}]: missing or empty 'folder'")
        else:
            if not KEBAB_RE.match(folder):
                errors.append(f"examples.json[{i}]: folder '{folder}' is not kebab-case")
            if folder in seen_folders:
                errors.append(f"examples.json[{i}]: duplicate folder '{folder}'")
            else:
                seen_folders.add(folder)
            if folder not in folders:
                errors.append(f"examples.json[{i}]: folder '{folder}' does not exist on disk")
        if extra:
            errors.append(f"examples.json[{i}]: unexpected keys {sorted(extra)}")

    unregistered = sorted(set(folders) - seen_folders)
    for folder in unregistered:
        errors.append(f"examples.json: example folder '{folder}' is not registered")


def validate_example_files(folder: str, errors: list[str]) -> None:
    path = REPO_ROOT / folder
    for required in ("workspace.yml", "workspace.lock", "README.md"):
        if not (path / required).is_file():
            errors.append(f"{folder}: missing {required}")

    assets_dir = REPO_ROOT / "assets" / folder
    if not assets_dir.is_dir():
        errors.append(f"{folder}: missing assets/{folder}/ directory")
        return
    pngs = list(assets_dir.glob("*.png"))
    if not pngs:
        errors.append(f"{folder}: assets/{folder}/ has no PNG screenshots")


def validate_workspace_yml(folder: str, errors: list[str]) -> None:
    path = REPO_ROOT / folder / "workspace.yml"
    if not path.is_file():
        return
    try:
        doc = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        errors.append(f"{folder}/workspace.yml: invalid YAML ({exc})")
        return
    if not isinstance(doc, dict):
        errors.append(f"{folder}/workspace.yml: top-level must be a mapping")
        return

    if doc.get("version") != "1.0":
        errors.append(f"{folder}/workspace.yml: version must be '1.0' (got {doc.get('version')!r})")

    workspace = doc.get("workspace")
    if not isinstance(workspace, dict):
        errors.append(f"{folder}/workspace.yml: missing 'workspace' mapping")
    else:
        if not isinstance(workspace.get("name"), str) or not workspace["name"].strip():
            errors.append(f"{folder}/workspace.yml: workspace.name must be a non-empty string")
        if not isinstance(workspace.get("description"), str) or not workspace["description"].strip():
            errors.append(f"{folder}/workspace.yml: workspace.description must be a non-empty string")

    signals = doc.get("signals")
    if not isinstance(signals, dict) or not signals:
        errors.append(f"{folder}/workspace.yml: 'signals' must be a non-empty mapping")
        signals = {}

    agents = doc.get("agents")
    if not isinstance(agents, dict) or not agents:
        errors.append(f"{folder}/workspace.yml: 'agents' must be a non-empty mapping")
        agents = {}

    jobs = doc.get("jobs")
    if not isinstance(jobs, dict) or not jobs:
        errors.append(f"{folder}/workspace.yml: 'jobs' must be a non-empty mapping")
        return

    for job_id, job in jobs.items():
        if not KEBAB_RE.match(job_id):
            errors.append(f"{folder}/workspace.yml: job id '{job_id}' must be kebab-case")
        if not isinstance(job, dict):
            errors.append(f"{folder}/workspace.yml: job '{job_id}' must be a mapping")
            continue
        validate_job(folder, job_id, job, signals, agents, errors)


def validate_job(
    folder: str,
    job_id: str,
    job: dict,
    signals: dict,
    agents: dict,
    errors: list[str],
) -> None:
    triggers = job.get("triggers") or []
    if not isinstance(triggers, list) or not triggers:
        errors.append(f"{folder}/workspace.yml: job '{job_id}' must declare at least one trigger")
    else:
        for t in triggers:
            if isinstance(t, dict) and "signal" in t and t["signal"] not in signals:
                errors.append(
                    f"{folder}/workspace.yml: job '{job_id}' triggers undefined signal '{t['signal']}'"
                )

    fsm = job.get("fsm")
    if not isinstance(fsm, dict):
        errors.append(f"{folder}/workspace.yml: job '{job_id}' missing fsm")
        return
    initial = fsm.get("initial")
    states = fsm.get("states")
    if initial != "idle":
        errors.append(f"{folder}/workspace.yml: job '{job_id}' fsm.initial must be 'idle'")
    if not isinstance(states, dict) or not states:
        errors.append(f"{folder}/workspace.yml: job '{job_id}' fsm.states must be a non-empty mapping")
        return
    if "idle" not in states:
        errors.append(f"{folder}/workspace.yml: job '{job_id}' fsm.states must define 'idle'")
    if not any(isinstance(s, dict) and s.get("type") == "final" for s in states.values()):
        errors.append(f"{folder}/workspace.yml: job '{job_id}' fsm has no final state")

    for state_name, state in states.items():
        if not isinstance(state, dict):
            continue
        for action in state.get("entry") or []:
            if isinstance(action, dict) and action.get("type") == "agent":
                agent_id = action.get("agentId")
                if agent_id and agent_id not in agents:
                    errors.append(
                        f"{folder}/workspace.yml: job '{job_id}' state '{state_name}' "
                        f"references undefined agent '{agent_id}'"
                    )


def main() -> int:
    errors: list[str] = []
    folders = discover_example_folders()
    if not folders:
        errors.append("repo: no example folders discovered at root")

    entries = load_examples_json(errors)
    validate_examples_json(entries, folders, errors)

    for folder in folders:
        validate_example_files(folder, errors)
        validate_workspace_yml(folder, errors)

    if errors:
        print(f"Found {len(errors)} validation error(s):", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    print(f"OK — {len(folders)} examples validated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
