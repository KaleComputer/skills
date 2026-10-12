# Skills

Skills follow the [Agent Skills](https://agentskills.io/) format.

```bash
npx skills add KaleComputer/skills
```

Claude Code: `/plugin marketplace add KaleComputer/skills`, then `/plugin install skills@kalecomputer`.
Codex: `codex plugin marketplace add KaleComputer/skills`, then `codex plugin add skills@kalecomputer`.

## purge

Audits, prunes, writes and reviews agent skills and agent context (`SKILL.md`, `AGENTS.md`,
`CLAUDE.md`, plugins), measuring what every session pays before and after. Explicit-only: run it
with `/purge` (`/skills:purge` as a plugin) or `$purge` in Codex.

On Kale's own agent tooling it took the skill descriptions loaded into every session from 9,489 to
1,905 characters (-80%, about 2,370 to 480 tokens), and skills from 27 to 21, 6 of them
explicit-only.
