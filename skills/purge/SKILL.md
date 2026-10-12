---
name: purge
description: Use when asked to audit, prune, write or review agent skills, SKILL.md files, AGENTS.md or CLAUDE.md files, plugins or other agent context.
disable-model-invocation: true
---

# Purge

Keep agent context small, routable and correct. Two modes share one standard:

- **Write or review one skill:** follow [Skill Shape](#skill-shape), the
  [Authoring Loop](#authoring-loop) and the [Review Checklist](#review-checklist). The output is a
  focused edit or review, not an essay about agents.
- **Purge a repository or machine:** audit the whole agent-facing surface with steps 1-7 and shrink
  it to the smallest reliable instruction set. Optimize for what every session pays, not for the
  smallest diff, and measure before and after so the result is a number, not an impression.

## Skill Shape

- `name` is lowercase kebab-case and matches the folder name.
- `description` is a routing condition only: it starts with `Use`, says when to load the skill in
  at most 30 words with distinct trigger branches, and is loaded into every session. What the skill
  does and how it differs from nearby skills belong in the body.
- A skill that only a human or a schedule should start is **explicit-only**: set
  `disable-model-invocation: true` in the frontmatter (Claude Code) and
  `policy.allow_implicit_invocation: false` in `agents/openai.yaml` (Codex). It then costs no
  context until someone invokes it by name.
- `SKILL.md` holds only what an agent needs at runtime: hard constraints, non-obvious failure
  handling and checkable completion criteria. Cut what the model already knows, history and
  implementation detail.
- Default to one lean `SKILL.md`. Add a `references/` file, linked directly from `SKILL.md`, only
  when selective loading saves context. Move deterministic or repeated work into `scripts/`.
  `assets/` hold templates or static files the output uses, not extra docs.
- Name capabilities, not temporary models, people or rollouts.

## Authoring Loop

1. Identify the repeated failure or repeated workflow the skill fixes.
2. Draft the `description` first; it is the routing contract.
3. Write the smallest useful body.
4. Add state checks before actions that depend on local setup.
5. Add a verify -> fix -> re-verify loop and say what evidence proves success.
6. Test prompts that should trigger the skill, nearby prompts that should not, and ambiguous
   prompts where another skill should win.
7. Run the repository's validation before calling it done.

## Review Checklist

- **Routing:** likely user phrases appear in the description; skills nobody should trigger
  implicitly are explicit-only.
- **Scope:** one skill, one concern; no bundled framework unless the workflow needs it.
- **Progressive disclosure:** the body is lean; details are linked one level deep.
- **Determinism:** fragile repeated steps are scripts, not hand-typed prose.
- **Failure modes:** missing tools, auth gaps, empty results and unsafe actions have explicit
  handling.
- **Safety:** no secrets or private user data; repository changes go through a branch and PR;
  payments, account or security changes, destructive actions and final submissions need explicit
  human approval.
- **Provenance:** adapted third-party material keeps its attribution and license.

## 1. Measure

Run the bundled script on the repository root before changing anything, and keep the output:

```bash
python3 <skill-dir>/scripts/measure-context.py --vendored <third-party-skill-dir> .
```

It reports, per skill and in total: the description text loaded into every session, the
`SKILL.md` size loaded on use, explicit-only skills, instruction files, `AGENTS.md` files hidden by
a sibling `CLAUDE.md`, explicit-only flags that disagree between harnesses, and descriptions over
30 words. After the changes merge, run it with `--before <old-ref> --after <new-ref>` for the
before/after table.

## 2. Inventory

1. Find every agent-facing file: skills, `AGENTS.md`, `CLAUDE.md`, agent definitions, generated
   mirrors, plugin manifests, marketplace files, references, scripts, evals and validation rules.
2. Read the repository's rules and how skills are distributed: which plugins are installed by
   default, where the marketplace points, and how installs learn about new versions.
3. Separate authored sources from generated mirrors and vendored third-party content.
4. Find real usage. Search session transcripts the human can share (for example
   `~/.claude/projects/*/*.jsonl`, `~/.codex/sessions/`) for each skill name, and list skills that
   never ran or only ran inside retired workflows. Identify consumers, compatibility paths and
   tests before calling anything obsolete.

## 3. Diagnose

Record a path, evidence and one or more labels for every finding:

- **Unused:** no recent invocation and no live consumer; the workflow it serves is retired.
- **Always-on but rare:** only ever run on an explicit human or scheduled request, yet its
  description loads in every session.
- **Broken:** invalid metadata, dead links, missing resources, impossible steps, failing validation.
- **Misrouted:** triggers are missing, vague, overlapping, or activate the wrong skill.
- **Bloated:** breaks [Skill Shape](#skill-shape), for example a description that explains what
  the skill does instead of when to use it.
- **Duplicated:** multiple files own the same workflow or truth.
- **Conflicting:** instructions disagree about authority, sequence, safety or completion.
- **Stale:** names, tools, models, people, paths, orgs or policies no longer match the system.
- **Hidden:** an instruction file that a harness never loads (for Claude Code, an `AGENTS.md` next
  to a `CLAUDE.md`, or a `CLAUDE.md` that points at `AGENTS.md` without `@AGENTS.md`).
- **Leaking:** an instruction file in a parent directory that every session below it loads.
- **Mis-distributed:** vendored or niche plugins installed for everyone by default, a marketplace
  that points at an old location, or versions that never change so installs never update.
- **Unverified:** important behavior has no static check, routing case or behavioral eval.

Do not report a finding without observable evidence.

## 4. Decide

Assign one verdict per item: `keep`, `fix`, `merge`, `split`, `explicit-only`, `opt-in` or `retire`.

- Prefer removing sediment over explaining around it.
- Make vendored or niche plugins **opt-in** instead of part of the default install.
- Keep one instruction file per directory. Prefer `AGENTS.md`, which Claude Code and Codex both
  read; delete a `CLAUDE.md` that only points at it.
- Make every content change reach installs: bump plugin versions on change (or let the commit
  identify the version), and point the marketplace at the current repository.
- Treat compatibility aliases as interfaces until their consumers are checked.

Present the verdicts to the human as choices, grouped by verdict, with the measured cost of each
item, before acting on anything destructive.

## 5. Change Safely

Ask for explicit approval before deleting, renaming, merging, retiring, making explicit-only or
opt-in any public skill, compatibility path or other externally consumed interface. Without
approval, make safe fixes and list the proposed changes separately.

Work on a branch and open a PR; never write directly to the default branch. Never expose or commit
secrets or private user data; transcripts used as usage evidence stay local and are summarized as
counts.

Add validation that keeps the result: description shape and length, explicit-only flags that agree
across harnesses, and no instruction file hidden by another.

## 6. Validate

1. **Static:** frontmatter, names, links, resources, scripts, generated mirrors, package discovery.
2. **Discovery:** start a fresh session with the changed plugins and list the skills it sees;
   explicit-only skills must be absent and still run when invoked by name.
3. **Routing:** the trigger, near-miss and ambiguous prompts from the
   [Authoring Loop](#authoring-loop) for each changed skill.
4. **Behavior:** for meaningful behavior changes, run at least three representative tasks against
   the previous or no-skill baseline in isolated context, and compare task success, routing
   precision, context loaded, invented work, safety violations and human corrections.
5. **Regression:** run existing tests and canaries after every fix.

## 7. Report

Return:

- the before/after table from `measure-context.py` (skills, explicit-only count, always-loaded
  description chars and estimated tokens, `SKILL.md` total, percentages);
- removed, added and renamed skills;
- findings with path, evidence and verdict;
- changes made, with PR links;
- validation and eval results, including the baseline;
- decisions still waiting on the human.

## Provenance

The skill-authoring guidance is adapted from David Ondrej's MIT-licensed
[effective-agent-skills](https://github.com/davidondrej/skills/tree/main/skills/skill-authoring/effective-agent-skills). The audit workflow is influenced by
Matt Pocock's
[writing-for-agents](https://github.com/mattpocock/skills/tree/main/skills/productivity/writing-for-agents)
and Anthropic's
[skill-creator](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/skill-creator/skills/skill-creator).
