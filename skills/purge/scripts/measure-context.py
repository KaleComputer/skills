#!/usr/bin/env python3
"""Measure how much agent context a repository's skills and instruction files cost.

Every installed skill's `description` is loaded into every session; the rest of
`SKILL.md` loads only when the skill runs. Explicit-only skills
(`disable-model-invocation: true` for Claude Code, `policy.allow_implicit_invocation:
false` in `agents/openai.yaml` for Codex) cost nothing until invoked.

Usage:
  measure-context.py [ROOT]                      measure the working tree
  measure-context.py --ref REF [ROOT]            measure a git ref
  measure-context.py --before REF --after REF    compare two git refs
  measure-context.py --usage GLOB [--usage GLOB] [--since DAYS]
                                                 count skill uses in session transcripts
  add --json for machine-readable output, --vendored DIR (repeatable) to report
  third-party skill folders separately.

--usage reads Claude Code and Codex JSONL transcripts (for example
'~/.claude/projects/**/*.jsonl', '~/.codex/sessions/**/*.jsonl') and counts, per
skill, the sessions that invoked it (Skill tool calls, slash commands, injected
skill files) and the sessions that only read a skills/<name>/SKILL.md with a
tool. It prints names, counts and dates only, never transcript content.

Token counts are estimates (characters / 4). Stdlib only.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import PurePosixPath

SKILL_RE = re.compile(r"(^|/)skills/[^/]+/SKILL\.md$")
INSTRUCTION_NAMES = {"AGENTS.md", "CLAUDE.md"}
SKIP_PARTS = {".git", "node_modules"}


class Tree:
    """Read files from the working tree or from a git ref."""

    def __init__(self, root: str, ref: str | None) -> None:
        self.root, self.ref = root, ref

    def files(self) -> list[str]:
        if self.ref:
            out = subprocess.run(
                ["git", "-C", self.root, "ls-tree", "-r", "--name-only", self.ref],
                capture_output=True, text=True, check=True,
            ).stdout
            return out.split("\n")
        found = []
        for base, dirs, names in os.walk(self.root):
            dirs[:] = [d for d in dirs if d not in SKIP_PARTS]
            for name in names:
                found.append(os.path.relpath(os.path.join(base, name), self.root))
        return found

    def read(self, path: str) -> str | None:
        if self.ref:
            done = subprocess.run(
                ["git", "-C", self.root, "show", f"{self.ref}:{path}"],
                capture_output=True, text=True,
            )
            return done.stdout if done.returncode == 0 else None
        try:
            with open(os.path.join(self.root, path), encoding="utf-8") as handle:
                return handle.read()
        except (OSError, UnicodeDecodeError):
            return None

    def is_mirror(self, path: str) -> bool:
        # Generated mirrors are symlinked skill folders; count each skill once.
        if self.ref:
            return False
        parent = os.path.join(self.root, os.path.dirname(path))
        return os.path.islink(parent)


def frontmatter(text: str) -> str:
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    return match.group(1) if match else ""


def description(front: str) -> str:
    match = re.search(r"^description:[ \t]*(.*?)(?=^\S|\Z)", front + "\n", re.S | re.M)
    if not match:
        return ""
    value = match.group(1).strip()
    if value[:1] in {">", "|"}:
        value = value[2:] if value[1:2] == "-" else value[1:]
    return " ".join(value.strip().strip("'\"").split())


def measure(tree: Tree, vendored: list[str]) -> dict:
    files = [f for f in tree.files() if f]
    skills, instructions = [], []
    for path in sorted(files):
        parts = PurePosixPath(path).parts
        if SKIP_PARTS & set(parts):
            continue
        if SKILL_RE.search(path) and not tree.is_mirror(path):
            text = tree.read(path)
            if text is None:
                continue
            front = frontmatter(text)
            policy = tree.read(str(PurePosixPath(path).parent / "agents/openai.yaml")) or ""
            desc = description(front)
            skills.append({
                "path": path,
                "name": PurePosixPath(path).parent.name,
                "vendored": any(path.startswith(v.rstrip("/") + "/") for v in vendored),
                "claude_explicit": re.search(r"^disable-model-invocation:\s*true\s*$", front, re.M) is not None,
                "codex_explicit": re.search(r"^\s*allow_implicit_invocation:\s*false\s*$", policy, re.M) is not None,
                "description_chars": len(desc),
                "description_words": len(desc.split()),
                "skill_chars": len(text),
            })
        elif parts and parts[-1] in INSTRUCTION_NAMES:
            text = tree.read(path)
            if text is not None:
                instructions.append({"path": path, "chars": len(text)})

    def totals(rows: list[dict]) -> dict:
        loaded = [r for r in rows if not r["claude_explicit"]]
        return {
            "skills": len(rows),
            "explicit_only": sum(r["claude_explicit"] for r in rows),
            "always_loaded_description_chars": sum(r["description_chars"] for r in loaded),
            "always_loaded_description_words": sum(r["description_words"] for r in loaded),
            "always_loaded_tokens_est": sum(r["description_chars"] for r in loaded) // 4,
            "skill_file_chars": sum(r["skill_chars"] for r in rows),
        }

    dirs: dict[str, set[str]] = {}
    for item in instructions:
        dirs.setdefault(str(PurePosixPath(item["path"]).parent), set()).add(PurePosixPath(item["path"]).name)
    return {
        "skills": skills,
        "own": totals([s for s in skills if not s["vendored"]]),
        "vendored": totals([s for s in skills if s["vendored"]]),
        "instruction_files": instructions,
        # Claude Code ignores AGENTS.md when CLAUDE.md sits in the same directory.
        "shadowed_agents_md": sorted(d for d, names in dirs.items() if names == INSTRUCTION_NAMES),
        "flag_mismatches": sorted(s["path"] for s in skills if s["claude_explicit"] != s["codex_explicit"]),
        "long_descriptions": sorted(s["path"] for s in skills if not s["vendored"] and s["description_words"] > 30),
    }


SKILL_PATH_RE = re.compile(r"skills/([A-Za-z0-9_.:-]+)/SKILL\.md")
INJECTED_RE = re.compile(r"<path>[^<]*?skills/([A-Za-z0-9_.:-]+)/SKILL\.md</path>")
COMMAND_RE = re.compile(r"<command-name>/?([A-Za-z0-9_.:-]+)</command-name>")
TOOL_CALL_TYPES = {"custom_tool_call", "function_call", "local_shell_call"}


def line_skills(entry: dict) -> tuple[set[str], set[str]]:
    """Skill names one transcript line invokes, and names it only reads via a tool."""
    invoked: set[str] = set()
    read: set[str] = set()
    payload = entry.get("payload")
    if isinstance(payload, dict):  # Codex
        if payload.get("type") in TOOL_CALL_TYPES:
            read.update(SKILL_PATH_RE.findall(json.dumps(payload)))
        elif payload.get("type") == "message" and payload.get("role") == "user":
            invoked.update(INJECTED_RE.findall(json.dumps(payload)))
        return invoked, read
    message = entry.get("message")
    if not isinstance(message, dict) or not isinstance(message.get("content"), (list, str)):
        return invoked, read
    content = message["content"]
    if message.get("role") == "user":
        invoked.update(COMMAND_RE.findall(content if isinstance(content, str) else json.dumps(content)))
        return invoked, read
    for item in content if isinstance(content, list) else []:
        if isinstance(item, dict) and item.get("type") == "tool_use":
            tool_input = item.get("input") or {}
            if item.get("name") == "Skill" and isinstance(tool_input.get("skill"), str):
                invoked.add(tool_input["skill"].lstrip("/"))
            else:
                read.update(SKILL_PATH_RE.findall(json.dumps(tool_input)))
    return invoked, read


def timestamp(entry: dict, fallback: float) -> float:
    value = entry.get("timestamp")
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
        except ValueError:
            pass
    return fallback


def usage(patterns: list[str], since_days: float | None) -> dict:
    cutoff = time.time() - since_days * 86400 if since_days else 0.0
    paths = sorted({p for pat in patterns for p in glob.glob(os.path.expanduser(pat), recursive=True)})
    skills: dict[str, dict] = {}
    sessions = {"claude": 0, "codex": 0}
    for path in paths:
        harness, active = None, False
        invoked: set[str] = set()
        read: set[str] = set()
        last: dict[str, float] = {}
        mtime = os.path.getmtime(path)
        with open(path, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    entry = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(entry, dict):
                    continue
                harness = harness or ("codex" if "payload" in entry else "claude")
                when = timestamp(entry, mtime)
                if when < cutoff:
                    continue
                active = True
                inv, rd = line_skills(entry)
                invoked |= inv
                read |= rd
                for name in inv | rd:
                    last[name] = max(last.get(name, 0.0), when)
        if harness is None or not active:
            continue
        sessions[harness] += 1
        for name in invoked | read:
            row = skills.setdefault(name, {"claude": 0, "codex": 0, "read_only": 0, "last": 0.0})
            if name in invoked:
                row[harness] += 1
            else:
                row["read_only"] += 1
            row["last"] = max(row["last"], last[name])
    for row in skills.values():
        row["last"] = datetime.fromtimestamp(row["last"]).strftime("%Y-%m-%d")
    return {"files": len(paths), "sessions": sessions, "since_days": since_days, "skills": skills}


def print_usage(data: dict) -> None:
    window = f"last {data['since_days']:g} days" if data["since_days"] else "all time"
    print(f"== usage ({window}): {data['sessions']['claude']} Claude Code and "
          f"{data['sessions']['codex']} Codex sessions in {data['files']} transcript files")
    print("  claude/codex: sessions that invoked the skill (Skill tool, slash command, injected file);")
    print("  read: sessions that only read its SKILL.md with a tool (loads, audits or edits). Subagents count separately.")
    print(f"  {'skill':40} {'claude':>6} {'codex':>6} {'read':>5}  last")
    rows = sorted(data["skills"].items(),
                  key=lambda kv: (-(kv[1]["claude"] + kv[1]["codex"]), -kv[1]["read_only"], kv[0]))
    for name, row in rows:
        print(f"  {name:40} {row['claude']:>6} {row['codex']:>6} {row['read_only']:>5}  {row['last']}")


def pct(before: int, after: int) -> str:
    return "n/a" if not before else f"{(after - before) / before * 100:+.0f}%"


def print_report(label: str, data: dict) -> None:
    own, vend = data["own"], data["vendored"]
    print(f"== {label}")
    print(f"  skills: {own['skills']} own ({own['explicit_only']} explicit-only), {vend['skills']} vendored")
    print(f"  always-loaded descriptions: {own['always_loaded_description_chars']} chars, "
          f"{own['always_loaded_description_words']} words, ~{own['always_loaded_tokens_est']} tokens "
          f"(+{vend['always_loaded_description_chars']} chars vendored)")
    print(f"  SKILL.md total (loaded on use): {own['skill_file_chars']} chars")
    print(f"  instruction files: {sum(i['chars'] for i in data['instruction_files'])} chars in "
          f"{len(data['instruction_files'])} files")
    for key, title in (("shadowed_agents_md", "AGENTS.md hidden by CLAUDE.md"),
                       ("flag_mismatches", "explicit-only flags disagree"),
                       ("long_descriptions", "descriptions over 30 words")):
        if data[key]:
            names = [PurePosixPath(p).parent.name if p.endswith("SKILL.md") else p for p in data[key]]
            print(f"  {title} ({len(names)}): {', '.join(names)}")
    print("  names: " + ", ".join(
        f"{s['name']}{'*' if s['claude_explicit'] else ''}" for s in data["skills"] if not s["vendored"]))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--ref")
    parser.add_argument("--before")
    parser.add_argument("--after")
    parser.add_argument("--vendored", action="append", default=[])
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--usage", action="append", metavar="GLOB",
                        help="transcript glob to count skill uses in (repeatable)")
    parser.add_argument("--since", type=float, metavar="DAYS", help="with --usage, only the last DAYS days")
    args = parser.parse_args(argv)

    if args.usage:
        data = usage(args.usage, args.since)
        if args.json:
            print(json.dumps(data, indent=2))
        else:
            print_usage(data)
        return 0

    if args.before or args.after:
        if not (args.before and args.after):
            parser.error("--before and --after go together")
        before = measure(Tree(args.root, args.before), args.vendored)
        after = measure(Tree(args.root, args.after), args.vendored)
        if args.json:
            print(json.dumps({"before": before, "after": after}, indent=2))
            return 0
        print_report(f"before {args.before}", before)
        print_report(f"after {args.after}", after)
        b, a = before["own"], after["own"]
        names_b = {s["name"] for s in before["skills"] if not s["vendored"]}
        names_a = {s["name"] for s in after["skills"] if not s["vendored"]}
        print("== change")
        print(f"  skills: {b['skills']} -> {a['skills']} (removed: {', '.join(sorted(names_b - names_a)) or 'none'}; "
              f"added: {', '.join(sorted(names_a - names_b)) or 'none'})")
        print(f"  always-loaded descriptions: {b['always_loaded_description_chars']} -> "
              f"{a['always_loaded_description_chars']} chars ({pct(b['always_loaded_description_chars'], a['always_loaded_description_chars'])})")
        print(f"  SKILL.md total: {b['skill_file_chars']} -> {a['skill_file_chars']} chars "
              f"({pct(b['skill_file_chars'], a['skill_file_chars'])})")
        return 0

    data = measure(Tree(args.root, args.ref), args.vendored)
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print_report(args.ref or args.root, data)
    return 0


if __name__ == "__main__":
    sys.exit(main())
