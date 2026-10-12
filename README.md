# Agent Skills

Agent skills from [Kale](https://github.com/KaleComputer). Skills are packaged instructions and
scripts that extend coding agents such as Claude Code and Codex.

Skills follow the [Agent Skills](https://agentskills.io/) format.

## Available Skills

### purge

Audits, prunes, writes and reviews agent skills and agent context: `SKILL.md` files, `AGENTS.md`
and `CLAUDE.md`, plugins and marketplaces. It measures what every session pays before and after,
labels each finding with evidence, proposes verdicts (`keep`, `fix`, `merge`, `explicit-only`,
`opt-in`, `retire`, ...) and asks before anything destructive. It is explicit-only, so it costs no
context until you invoke it.

**Use when:**

- "Purge the skills in this repo"
- Shrinking the skill descriptions loaded into every session
- Writing a new skill or reviewing an existing one
- Debugging why a skill does or does not trigger
- Finding hidden, duplicated or stale `AGENTS.md` / `CLAUDE.md` instructions

**Example:** on Kale's internal agent tooling repository, one purge took the skills loaded into
every session from 9,489 to 1,905 description characters (-80%, about 2,370 to 480 tokens). Skills
went from 27 (none explicit-only) to 21 (6 explicit-only), and total `SKILL.md` size from 126,495
to 86,223 characters (-32%). Measure your own repository with the bundled script:

```bash
python3 skills/purge/scripts/measure-context.py /path/to/repo
python3 skills/purge/scripts/measure-context.py --before <old-ref> --after <new-ref> /path/to/repo
```

## Installation

```bash
npx skills add KaleComputer/skills --skill purge
```

Or as a Claude Code plugin:

```
/plugin marketplace add KaleComputer/skills
/plugin install skills@kalecomputer
```

Or as a Codex plugin:

```bash
codex plugin marketplace add KaleComputer/skills
codex plugin add skills@kalecomputer
```

## Usage

Explicit-only skills run when you ask for them by name:

- Claude Code: `/skills:purge` (plugin) or `/purge` (`npx skills`)
- Codex: `$skills:purge` (plugin) or `$purge` (`npx skills`)
- Any agent: "run the purge skill"

## Skill Structure

Each skill lives in `skills/<name>/` and contains:

- `SKILL.md` - instructions for the agent
- `scripts/` - helper scripts (optional)
- `references/` - supporting docs loaded on demand (optional)
- `agents/openai.yaml` - Codex policy (optional)

See [AGENTS.md](AGENTS.md) for how to add a skill.

## License

[MIT](LICENSE). Skills adapted from third-party work keep their attribution in the skill's
Provenance section.
