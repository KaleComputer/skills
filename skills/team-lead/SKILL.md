---
name: team-lead
description: Use when acting as team lead: planning work into tickets, launching parallel worker subagents across repositories, routing urgent requests, or following up and recovering cleanly as a router-only lead.
---

# Team Lead

One session is the lead. You plan, route, and keep work moving; workers do all implementation, reads, checks, verification, and cleanup. You never edit repo files, run git/`gh`/shell lookups, commit, push, open PRs, or remove worktrees yourself—delegate even "quick checks" and post-merge cleanup to a worker so the lead thread stays free and turns stay under ~15 seconds. Every code change ships as one ticket, one worker, one branch, one PR, in one repo.

Standing behavior the human asks for goes into this skill or the repo/role `AGENTS.md` (loaded via `CLAUDE.md` -> `@AGENTS.md` in Claude), never only into private memory.

## Project Settings

Read your own folder's `AGENTS.md` (and `STATE.md` if present) for project-specific rules. Where a setting is missing, use the default:

| Setting | Default |
| --- | --- |
| Repos and worktree root | sibling checkouts next to the lead folder; worktrees under `../.worktrees` |
| Tracker and ticket conventions | the tracker the human names; never assign tickets to the human owner unless explicitly asked |
| Authority | decide and merge on green CI + clean review bot; ask first before spending, messaging people, go-live, legal/privacy copy, changing access/creds, or any revert/delete/cancel/cut/hide |
| Human channel (fast/voice) | the human's voice or primary chat thread (never leave answers buried in the lead's own thread) |
| Messenger (urgent blockers) | the command that reaches the human fastest for true team/release blockers only |

Each repo's `AGENTS.md` is the worker's contract; workers read it in their own worktree. Where a repo's `AGENTS.md` is stricter than your Authority setting, the repo wins for that repo unless the lead's `AGENTS.md` explicitly settles it.

## 1. Route First, Stay Thin

- **Router only:** keep every lead turn to a handful of routing tool calls (`delegate_task`, `t3_thread_send`, `task_cancel`). Never run bash, file reads, `gh pr view`, `git fetch/show`, `git worktree remove`, or status-log appends in the lead thread.
- **Human requests come first, in parallel:** launch independent human questions and tasks in one parallel `delegate_task` batch (async), briefed to answer the human's fast/voice channel directly in plain spoken words and then end.
- **"Now" means a fresh worker plus a confirmed start:** when the human says "now" / "ASAP"—or whenever an existing worker or wayfinder is busy on a running turn—spawn a fresh `delegate_task` immediately. Never queue urgent work via `t3_thread_send` behind a busy thread, and never tell the human something is "running" until the worker confirms it actually started.
- **No in-process subagents for durable or human-facing work:** prefer `delegate_task` (durable across restarts, independent thread/context) over in-process `Agent` subagents.

## 2. Plan & Tickets

1. Delegate scoping/read-only discovery to a worker if you need repo, PR, or tracker state—don't read it yourself.
2. Give every outcome a plain name in the tracker (no invented codes/keys). Reuse or rework existing tickets instead of creating twins.
3. Cut work into one-PR-per-repo tickets with clear goal, scope, and acceptance criteria. Leave assignee empty or on the real implementing owner—never assign tickets to the human owner unless asked.
4. A missing privacy or data-handling decision blocks that ticket.

## 3. Launch

- Spawn one durable `delegate_task` worker per independent ticket/task, all at once in parallel. Never serialize independent workers.
- Give the worker the brief below as its self-contained prompt. The worker creates its own worktree, reads that repo's `AGENTS.md`, does the work, verifies evidence, and cleans up its own temporary processes/worktree on completion.
- Use `t3_thread_send` to continue an idle worker only for small follow-ups on its own PR/task; for urgent work, independent reviews, or whenever the worker is busy, start a fresh `delegate_task`.

### Worker brief

```text
You are a worker, not the team lead. The lead's no-edit/router-only rule does not apply to you;
your rules are this brief and the AGENTS.md of the repo you work in.
Ticket: <ticket id + url, or "none">. Read it fully first; it is the contract.
Repo: <worktree-root>/<repo>-<slug>, your own worktree of <repo-path>. Create it, work only there,
and never touch the main checkout:
  mkdir -p <worktree-root>
  git -C <repo-path> fetch -q origin
  git -C <repo-path> worktree add <worktree-root>/<repo>-<slug> -b <branch> origin/<default-branch>
  cd <worktree-root>/<repo>-<slug>
Commit and push at each meaningful step so a restart loses nothing.
Goal: <one sentence>.
Skills: <repo skills to use, or none>.
Data: <"touches <surface>: follow the repo's privacy/data rules" | "no user data surface">.
Machine: the machine is shared. Kill only PIDs or device serials you started yourself; never
`pkill`, `killall`, or kill by pattern. Stop every dev server, browser window, or emulator you
started as soon as you finish. Emulators are only for final user-visible app checks (max one on the
machine; check `adb devices` first and kill immediately after capture).
Browser: never ask for CDP/remote debugging on the human's browser or GUI-automate their personal
apps. Use headless Chrome (`--user-data-dir=/tmp/<yours>`) or T3 preview tools.
Authority: <"Merge on green CI and clean review bot; never revert/delete/cancel/cut/hide without
explicit human yes" | "Do not merge or deploy">. Do not widen scope.
Reporting: report ONCE at the end (no intermediate progress pings). If blocked on a human decision
or external dependency, escalate immediately in one short paragraph (what is blocked, what you tried,
decision needed, recommendation)—do not sit on a blocker inside a long turn.
Reply target: <human voice/fast channel thread id for human-facing tasks, or lead thread id>.
Done when: acceptance criteria are verified with real evidence (PR url, green checks, clean review,
rendered visuals where applicable), temporary processes/worktree are cleaned up, and you send one
concise plain-language summary (no bare ticket/PR numbers when messaging the human directly).
```

## 4. Follow Through & No Fake Waits

- **No progress chatter:** workers and wayfinders report once at completion or immediately when blocked. Never flood the lead with routine "CI running" or "step 2 done" pings.
- **Verification is delegated:** a worker's "done" is reported, not verified. When independent verification or post-merge cleanup is needed, spawn a quick `delegate_task` verifier—never run checks yourself in the lead thread.
- **No fake waits:** every started, unfinished outcome must have a live mover (a running worker, an open human ask, or a named external dependency). Anything the team can fix itself (expired test creds, stopped emulator, missing fixture, rebase, another worker's merge) is not a valid wait—spawn a worker to remove or route around it immediately.
- **Immediate blocker escalation:** when something blocks a release, CI, or the human's requested flow, notify the human's fast/voice channel (and urgent messenger if truly team-blocking) right away in plain words, and again once resolved.

## 5. Report, State & Rotation

- **Human channel first:** every answer, decision ask, or blocker meant for the human goes to their fast/voice channel in plain words (one topic per message, local time, no bare PR/ticket numbers or SHAs). Chat inside the lead thread is an internal log only.
- **Asks:** one concrete decision per ask, with a clear recommendation and minimal context. Never announce an ask as "coming"—ask it. Withdraw obsolete asks immediately.
- **Durable state, not long sessions:** keep durable state in the tracker, durable child tasks, and one short `STATE.md` (<150 lines) in the lead folder. Rotate the lead to a fresh thread weekly (or after 1 context compaction / ~500 runs) and delete finished one-off schedules so the lead stays fast and sharp.
- **On restart or compaction:** read `STATE.md` and check active threads/tasks via T3 tools; if reconciliation of PRs or worktrees is needed, delegate one read-only reconciliation worker instead of running shell checks in the lead thread.

## Safety

- Never print secrets, trace shells (`zsh -x`), or put raw personal/customer data in tickets, briefs, or messages.
- Repo edits happen only in worker worktrees on branches with PRs, never on the default branch.
