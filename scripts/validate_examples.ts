#!/usr/bin/env -S deno run --allow-read --allow-env
/**
 * Structural validator for friday-studio-examples.
 *
 * Repo-policy checks (handled here):
 *   - examples.json is well-formed; each entry has a unique kebab-case folder and name
 *   - every registered folder exists with workspace.yml, workspace.lock, README.md
 *   - every example folder at the repo root is registered in examples.json
 *   - every example has an assets/<folder>/ directory with at least one PNG
 *
 * Schema checks are delegated to @atlas/config's validateWorkspace(), which runs:
 *   - WorkspaceConfigSchema.safeParse (structural: types, enums, mutual-exclusion)
 *   - reference integrity (agent ids, tool refs, memory refs)
 *   - semantic warnings (dead signals, orphan agents, cron parse, http path collisions)
 *
 * Exits non-zero if any errors are found. Warnings are printed but do not fail CI.
 */

import { parse as parseYaml } from "@std/yaml";
import { validateWorkspace } from "@atlas/config";

const REPO_ROOT = new URL("..", import.meta.url).pathname.replace(/\/$/, "");
const KEBAB_RE = /^[a-z0-9]+(-[a-z0-9]+)*$/;

interface ExamplesEntry {
  name?: unknown;
  folder?: unknown;
  [k: string]: unknown;
}

function discoverExampleFolders(): string[] {
  const folders: string[] = [];
  for (const entry of Deno.readDirSync(REPO_ROOT)) {
    if (!entry.isDirectory) continue;
    if (entry.name.startsWith(".")) continue;
    if (!fileExists(`${REPO_ROOT}/${entry.name}/workspace.yml`)) continue;
    folders.push(entry.name);
  }
  folders.sort();
  return folders;
}

function loadExamplesJson(errors: string[]): ExamplesEntry[] {
  const path = `${REPO_ROOT}/examples.json`;
  let text: string;
  try {
    text = Deno.readTextFileSync(path);
  } catch {
    errors.push("examples.json: missing at repo root");
    return [];
  }
  try {
    const data = JSON.parse(text);
    if (!Array.isArray(data)) {
      errors.push("examples.json: must be a JSON array");
      return [];
    }
    return data as ExamplesEntry[];
  } catch (exc) {
    errors.push(`examples.json: invalid JSON (${(exc as Error).message})`);
    return [];
  }
}

function validateExamplesJson(
  entries: ExamplesEntry[],
  folders: string[],
  errors: string[],
): void {
  const seenNames = new Set<string>();
  const seenFolders = new Set<string>();
  entries.forEach((entry, i) => {
    if (typeof entry !== "object" || entry === null || Array.isArray(entry)) {
      errors.push(`examples.json[${i}]: must be an object`);
      return;
    }
    const { name, folder } = entry;
    const extra = Object.keys(entry).filter((k) => k !== "name" && k !== "folder").sort();

    if (typeof name !== "string" || !name.trim()) {
      errors.push(`examples.json[${i}]: missing or empty 'name'`);
    } else if (seenNames.has(name)) {
      errors.push(`examples.json[${i}]: duplicate name '${name}'`);
    } else {
      seenNames.add(name);
    }

    if (typeof folder !== "string" || !folder.trim()) {
      errors.push(`examples.json[${i}]: missing or empty 'folder'`);
    } else {
      if (!KEBAB_RE.test(folder)) {
        errors.push(`examples.json[${i}]: folder '${folder}' is not kebab-case`);
      }
      if (seenFolders.has(folder)) {
        errors.push(`examples.json[${i}]: duplicate folder '${folder}'`);
      } else {
        seenFolders.add(folder);
      }
      if (!folders.includes(folder)) {
        errors.push(`examples.json[${i}]: folder '${folder}' does not exist on disk`);
      }
    }

    if (extra.length > 0) {
      errors.push(`examples.json[${i}]: unexpected keys ${JSON.stringify(extra)}`);
    }
  });

  for (const folder of folders) {
    if (!seenFolders.has(folder)) {
      errors.push(`examples.json: example folder '${folder}' is not registered`);
    }
  }
}

function fileExists(path: string): boolean {
  try {
    return Deno.statSync(path).isFile;
  } catch {
    return false;
  }
}

function dirExists(path: string): boolean {
  try {
    return Deno.statSync(path).isDirectory;
  } catch {
    return false;
  }
}

function validateExampleFiles(folder: string, errors: string[]): void {
  const base = `${REPO_ROOT}/${folder}`;
  for (const required of ["workspace.yml", "workspace.lock", "README.md"]) {
    if (!fileExists(`${base}/${required}`)) {
      errors.push(`${folder}: missing ${required}`);
    }
  }
  const assetsDir = `${REPO_ROOT}/assets/${folder}`;
  if (!dirExists(assetsDir)) {
    errors.push(`${folder}: missing assets/${folder}/ directory`);
    return;
  }
  let pngCount = 0;
  for (const entry of Deno.readDirSync(assetsDir)) {
    if (entry.isFile && entry.name.toLowerCase().endsWith(".png")) pngCount++;
  }
  if (pngCount === 0) {
    errors.push(`${folder}: assets/${folder}/ has no PNG screenshots`);
  }
}

function validateWorkspaceYml(
  folder: string,
  errors: string[],
  warnings: string[],
): void {
  const path = `${REPO_ROOT}/${folder}/workspace.yml`;
  if (!fileExists(path)) return;

  let doc: unknown;
  try {
    doc = parseYaml(Deno.readTextFileSync(path));
  } catch (exc) {
    errors.push(`${folder}/workspace.yml: invalid YAML (${(exc as Error).message})`);
    return;
  }

  const report = validateWorkspace(doc);
  for (const issue of report.errors) {
    const loc = issue.path ? `${issue.path}: ` : "";
    errors.push(`${folder}/workspace.yml: ${loc}${issue.message} [${issue.code}]`);
  }
  for (const issue of report.warnings) {
    const loc = issue.path ? `${issue.path}: ` : "";
    warnings.push(`${folder}/workspace.yml: ${loc}${issue.message} [${issue.code}]`);
  }

  // House-style: job IDs must be kebab-case. The canonical schema accepts
  // any MCP-compliant tool name ([a-zA-Z0-9_-]+); examples should be uniform.
  if (typeof doc === "object" && doc !== null && "jobs" in doc) {
    const jobs = (doc as { jobs?: unknown }).jobs;
    if (typeof jobs === "object" && jobs !== null) {
      for (const jobId of Object.keys(jobs)) {
        if (!KEBAB_RE.test(jobId)) {
          errors.push(
            `${folder}/workspace.yml: job id '${jobId}' must be kebab-case`,
          );
        }
      }
    }
  }
}

function main(): number {
  const errors: string[] = [];
  const warnings: string[] = [];
  const folders = discoverExampleFolders();
  if (folders.length === 0) {
    errors.push("repo: no example folders discovered at root");
  }

  const entries = loadExamplesJson(errors);
  validateExamplesJson(entries, folders, errors);

  for (const folder of folders) {
    validateExampleFiles(folder, errors);
    validateWorkspaceYml(folder, errors, warnings);
  }

  if (warnings.length > 0) {
    console.error(`Found ${warnings.length} warning(s):`);
    for (const w of warnings) console.error(`  - ${w}`);
  }
  if (errors.length > 0) {
    console.error(`Found ${errors.length} validation error(s):`);
    for (const e of errors) console.error(`  - ${e}`);
  }
  // Examples should be exemplary: any warning is a defect users would inherit.
  if (errors.length > 0 || warnings.length > 0) return 1;
  console.log(`OK — ${folders.length} examples validated.`);
  return 0;
}

Deno.exit(main());
