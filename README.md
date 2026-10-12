# Skills

The agent skills we use at Kale.

## Installation

```bash
npx skills add KaleComputer/skills
```

Or as a plugin:

```bash
# Claude Code
/plugin marketplace add KaleComputer/skills
/plugin install skills@kalecomputer

# Codex
codex plugin marketplace add KaleComputer/skills
codex plugin add skills@kalecomputer
```

## Skills

### purge

Every installed skill puts its description into every agent session, and every `AGENTS.md` or
`CLAUDE.md` line is read before the agent does anything. Over time skills pile up, overlap, go
stale and trigger at the wrong moment, so each session pays for context it never uses and agents
pick the wrong workflow. Purge measures what your agent context costs per session, finds unused,
duplicated, stale, hidden and misrouted instructions with evidence, checks which skills were
actually used and which lack the tools or credentials to run, proposes what to keep, fix,
merge, make explicit-only or retire, asks before anything destructive, and reports the
before/after numbers. It also writes and reviews single skills.

**Use when:**

- Your skill list or `AGENTS.md` files have grown and sessions feel slow or unfocused
- Agents pick the wrong skill, or a skill does not trigger
- You are writing a new skill or reviewing one before shipping it
- You want to know how much context your skills cost per session
- You want to know which skills are actually used, and which cannot run where they are installed

**When to run:** after adding or changing several skills, before rolling skills out to a team, and
on a schedule (monthly works for most repositories; weekly if many people or agents add skills).

Purge is explicit-only, so it costs no context until you run it: `/purge` (`/skills:purge` as a
plugin) in Claude Code, `$purge` in Codex.

### team-lead

Agents ship more when one session plans and others build, but a single agent that both plans and
edits loses track, and parallel agents trip over each other in one checkout. Team-lead makes one
session the lead: it plans from your issue tracker and docs, cuts the work into one-ticket,
one-PR, one-repo tickets, asks you every open question in one batch, and launches nothing until
you approve. Then it runs worker subagents, each in its own git worktree, following that repo's
`AGENTS.md` and review loop, and reports one line per ticket. The lead never edits, merges or
deploys. Repos, tracker, worktree root and review bot come from the lead folder's `AGENTS.md`.

**Use when:**

- You want one agent session to plan a project or milestone and delegate the implementation
- A feature spans several repositories and needs one PR per repo, in order
- You run several coding agents in parallel and want them isolated in worktrees

**Setup:** give the lead its own folder with an `AGENTS.md` that says to always use the
`team-lead` skill and lists the project settings. The model can load it on its own.

---

Skills follow the [Agent Skills](https://agentskills.io/) format.
