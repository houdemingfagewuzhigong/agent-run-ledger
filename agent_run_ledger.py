#!/usr/bin/env python3
"""Keep a tamper-light ledger of what coding agents changed in a repo."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


LEDGER_DIR = ".agent-ledger"
LEDGER_FILE = "runs.json"


@dataclass
class RunEntry:
    id: str
    timestamp: str
    agent: str
    note: str
    branch: str
    commit: str
    dirty_files: list[str]
    diff_stats: dict[str, int]
    risk_flags: list[str]


def run_git(args: list[str], cwd: Path) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"git {' '.join(args)} failed")
    return proc.stdout.strip()


def repo_root(path: Path) -> Path:
    try:
        return Path(run_git(["rev-parse", "--show-toplevel"], path)).resolve()
    except RuntimeError as exc:
        raise SystemExit(f"Not a git repository: {path}") from exc


def ledger_path(root: Path) -> Path:
    return root / LEDGER_DIR / LEDGER_FILE


def load_entries(root: Path) -> list[RunEntry]:
    path = ledger_path(root)
    if not path.exists():
        return []
    return [RunEntry(**item) for item in json.loads(path.read_text())]


def save_entries(root: Path, entries: list[RunEntry]) -> None:
    path = ledger_path(root)
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps([asdict(entry) for entry in entries], indent=2) + "\n")


def current_branch(root: Path) -> str:
    return run_git(["branch", "--show-current"], root) or "detached"


def current_commit(root: Path) -> str:
    try:
        return run_git(["rev-parse", "--short", "HEAD"], root)
    except RuntimeError:
        return "unborn"


def dirty_files(root: Path) -> list[str]:
    output = run_git(["status", "--short"], root)
    return [line[3:] for line in output.splitlines() if line.strip()]


def diff_stats(root: Path) -> dict[str, int]:
    output = run_git(["diff", "--numstat"], root)
    stats = {"files": 0, "insertions": 0, "deletions": 0}
    for line in output.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        added, removed, _path = parts[:3]
        stats["files"] += 1
        stats["insertions"] += int(added) if added.isdigit() else 0
        stats["deletions"] += int(removed) if removed.isdigit() else 0
    return stats


def risk_flags(files: list[str], stats: dict[str, int]) -> list[str]:
    flags: list[str] = []
    lower_files = [item.lower() for item in files]
    if any(name.endswith((".env", ".pem", ".key", ".token")) for name in lower_files):
        flags.append("secret-adjacent file changed")
    if any("package-lock.json" in name or "pnpm-lock.yaml" in name or "poetry.lock" in name for name in lower_files):
        flags.append("dependency lockfile changed")
    if stats["files"] >= 20 or stats["insertions"] + stats["deletions"] >= 1000:
        flags.append("large change set")
    if any(name.startswith(".github/workflows/") for name in lower_files):
        flags.append("workflow changed")
    return flags


def new_entry(root: Path, agent: str, note: str) -> RunEntry:
    timestamp = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    files = dirty_files(root)
    stats = diff_stats(root)
    return RunEntry(
        id=timestamp.replace(":", "").replace("+", "Z"),
        timestamp=timestamp,
        agent=agent,
        note=note,
        branch=current_branch(root),
        commit=current_commit(root),
        dirty_files=files,
        diff_stats=stats,
        risk_flags=risk_flags(files, stats),
    )


def render_html(entries: list[RunEntry]) -> str:
    rows = []
    for entry in reversed(entries):
        flags = ", ".join(entry.risk_flags) or "none"
        files = "<br>".join(html.escape(path) for path in entry.dirty_files[:12]) or "clean"
        rows.append(
            f"<tr><td>{html.escape(entry.timestamp)}</td><td>{html.escape(entry.agent)}</td>"
            f"<td>{html.escape(entry.branch)}@{html.escape(entry.commit)}</td>"
            f"<td>{entry.diff_stats['files']} files, +{entry.diff_stats['insertions']} "
            f"-{entry.diff_stats['deletions']}</td><td>{html.escape(flags)}</td>"
            f"<td>{html.escape(entry.note)}</td><td>{files}</td></tr>"
        )
    return """<!doctype html>
<meta charset="utf-8">
<title>Agent Run Ledger</title>
<style>
body{font:14px system-ui,sans-serif;margin:32px;color:#17202a;background:#f7f8fb}
h1{font-size:28px}table{border-collapse:collapse;width:100%;background:white}
th,td{border:1px solid #d8dee9;padding:10px;text-align:left;vertical-align:top}
th{background:#eef2f7}.risk{font-weight:700}
</style>
<h1>Agent Run Ledger</h1>
<p>Review what each coding agent changed before you merge or hand the repo to another agent.</p>
<table><thead><tr><th>Time</th><th>Agent</th><th>Ref</th><th>Diff</th><th>Risk</th><th>Note</th><th>Files</th></tr></thead>
<tbody>
""" + "\n".join(rows) + "\n</tbody></table>\n"


def sarif(entries: list[RunEntry]) -> dict:
    results = []
    for entry in entries:
        for flag in entry.risk_flags:
            results.append(
                {
                    "ruleId": "agent-run-ledger.risk",
                    "level": "warning",
                    "message": {"text": f"{entry.agent} run flagged: {flag}"},
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {"uri": LEDGER_DIR + "/" + LEDGER_FILE}
                            }
                        }
                    ],
                }
            )
    return {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [
            {
                "tool": {"driver": {"name": "Agent Run Ledger", "rules": []}},
                "results": results,
            }
        ],
    }


def cmd_snapshot(args: argparse.Namespace) -> int:
    root = repo_root(Path(args.path).resolve())
    entries = load_entries(root)
    entry = new_entry(root, args.agent, args.note)
    entries.append(entry)
    save_entries(root, entries)
    print(f"recorded {entry.id}: {len(entry.dirty_files)} dirty files, flags={entry.risk_flags or ['none']}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    root = repo_root(Path(args.path).resolve())
    entries = load_entries(root)
    output = Path(args.output)
    output.write_text(render_html(entries))
    print(f"wrote {output}")
    return 0


def cmd_export(args: argparse.Namespace) -> int:
    root = repo_root(Path(args.path).resolve())
    entries = load_entries(root)
    data = sarif(entries) if args.format == "sarif" else [asdict(entry) for entry in entries]
    print(json.dumps(data, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Track what coding agents changed between handoffs.")
    sub = parser.add_subparsers(required=True)

    snap = sub.add_parser("snapshot", help="record the current repo state")
    snap.add_argument("--agent", required=True, help="agent name, such as codex or cursor")
    snap.add_argument("--note", default="", help="short human note for this run")
    snap.add_argument("--path", default=".", help="repo path")
    snap.set_defaults(func=cmd_snapshot)

    report = sub.add_parser("report", help="render an HTML timeline")
    report.add_argument("--path", default=".", help="repo path")
    report.add_argument("--output", default="agent-ledger.html", help="HTML output path")
    report.set_defaults(func=cmd_report)

    export = sub.add_parser("export", help="print JSON or SARIF")
    export.add_argument("--path", default=".", help="repo path")
    export.add_argument("--format", choices=["json", "sarif"], default="json")
    export.set_defaults(func=cmd_export)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
