# AGENTS.md

Guidance for coding agents working in this repository.

## Repository Overview

Public agent skills from Kale, published for anyone to install with `npx skills add
KaleComputer/skills` or as a Claude Code / Codex plugin. Everything here is public: no secrets,
private user data, internal names, tickets or internal paths.

## Adding a Skill

```
skills/
  <skill-name>/           kebab-case, matches `name` in SKILL.md
    SKILL.md              required, exact filename
    scripts/              optional, kebab-case file names
    references/           optional, linked directly from SKILL.md
    agents/openai.yaml    optional, Codex policy
```

- **Frontmatter:** `name` and `description`. The description is a routing condition only: it
  starts with `Use when`, at most 30 words, and says when to load the skill, not what it does.
- **Explicit-only:** if only a human should start the skill, add `disable-model-invocation: true`
  to the frontmatter and `policy.allow_implicit_invocation: false` in `agents/openai.yaml`.
- **Body:** only what an agent needs at runtime. Keep `SKILL.md` lean (well under 500 lines); move
  detail to `references/` and repeatable steps to `scripts/`. Reference scripts by path relative to
  the skill folder.
- **Scripts:** no install step. Prefer the standard library, write status to stderr and results to
  stdout, and support `--help`.
- **Provenance:** adapted third-party material keeps its attribution and license in a Provenance
  section.
- **README:** add the skill to `README.md` with a short summary and **Use when** bullets.

Run the `purge` skill's review checklist on a new skill before opening the PR.

## Checks

```bash
claude plugin validate .
npx skills add . --list
python3 skills/purge/scripts/measure-context.py .
```

The plugin manifests (`.claude-plugin/`, `.codex-plugin/`, `.agents/plugins/marketplace.json`)
pick up every folder under `skills/` automatically. They carry no version, so each commit is a new
version; do not add one.

## Workflow

Work on a branch and open a pull request; do not push to `main`.
