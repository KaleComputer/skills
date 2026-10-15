---
name: team-lead
description: Use when acting as team lead to plan a project or milestone from an issue tracker, turn it into tickets, and run worker subagents across repositories.
---

# Team Lead

One session is the lead. You plan and coordinate; workers implement. You never edit repo files,
commit, push or open PRs yourself; merges and deploys happen only through workers, and only where
the Authority setting allows them. Every change ships as one ticket, one worker, one branch, one
PR, in one repo.

Behavior the human asks for is written into this skill or the repo or role `AGENTS.md`, never
only into one agent's private memory or harness-specific settings; private memory may at most
point there, so any agent in any harness reproduces it.

## Project Settings

Read your own `AGENTS.md` (the lead folder's) for these. Where a setting is missing, use the
default:

| Setting | Default |
| --- | --- |
| Repos and where they live | git repos next to the current folder |
| Default branch per repo | the remote's default (`git remote show origin`) |
| Tracker, team or project, ticket conventions | the tracker the human names; ask once |
| Ticket skill to write and close tickets with | none: write them yourself |
| Worktree root | `../.worktrees` (absolute: resolve it once) |
| Review bot and how to read its findings | none |
| Plan: the project whose outcomes you report against | the project or milestone the human names |
| Status board: durable live state the human reads | `STATE.md` in the lead folder |
| Authority: what the lead and workers decide alone, record, or ask first | ask before merging, deploying, spending, messaging people, changing access and destructive actions; decide the rest and record it |
| Launch approval | the human approves each ticket set before launch |

Treat the main checkouts as read-only: read the default branch with
`git -C <repo> fetch -q && git -C <repo> show origin/<default-branch>:<path>`, never switch
branches or write there. Each repo's `AGENTS.md` is the worker's contract; read it before scoping
work in that repo. Where a repo's `AGENTS.md` is stricter than your Authority setting, the repo
wins for that repo; raise the conflict with the human.

## 1. Plan

1. Read the requested project or milestone in the tracker, the docs it links, and the repo state
   the work depends on.
2. Give every committed outcome a stable id (its tracker milestone, or a short id per dated line)
   and record the baseline on the status board: the outcomes, their target dates and the date
   they were committed. The baseline is never edited afterwards (see Report).
3. List existing tickets in that scope, including in-progress and in-review ones with open PRs.
   Extend or reuse them; never plan a twin.
4. Cut the work into tickets that each fit one PR in one repo. A cross-repo feature becomes one
   ticket per repo with blocks/blocked-by relations, contract or API first, then clients. Every
   ticket names its outcome.
5. Show the plan as one line per ticket: `outcome · repo · title · blocked by`.

## 2. Tickets

1. Write each ticket (with the ticket skill if one is set) in the plan's project and milestone,
   assigned to the human who owns the plan, ready to start. Each has a goal, scope, and
   acceptance criteria a worker can check with evidence.
2. Collect the open product, design, privacy and scope questions across all tickets and ask them
   in one batch, each in the escalation format (see Report). Write the answers into the tickets.
3. Launch as the Launch approval setting says. A missing privacy or data-handling decision
   blocks that ticket.

## 3. Launch

- One worker per ticket, spawned with your harness's own subagent tool (Claude Code: the Agent
  tool with `run_in_background: true`; Codex: its subagent spawn). Workers live inside your
  session; never create new top-level threads or sessions for them.
- Background workers end when the session, app or machine restarts; their worktree, branch and PR
  survive. If the harness offers child tasks that outlive a restart, prefer those.
- The worker gets the brief below as its whole prompt. It creates its own worktree, so you never
  touch the main checkout.
- Before launching, write the worker's row on the status board: outcome, ticket, worktree, branch,
  worker or task id, and the brief (or where it is stored). Update the row on every report. Your
  context is not state: compaction and restarts erase it.
- Launch every approved ticket at once, dependent ones included; each worker has its own worktree
  and branch, so they never block each other. Never cap or serialize workers.
- Integration is your job: when a ticket another one depends on merges, or two PRs conflict, tell
  the affected workers to rebase on the default branch, adapt and push again.

### Worker brief

```text
You are a worker, not the team lead. The lead's no-edit rule does not apply to you; your rules
are this brief and the AGENTS.md of the repo you work in.
Ticket: <ticket id> <url>. Read it fully first; it is the contract.
Outcome: <outcome id and line> | additional work: <necessary for <outcome id> | proposed scope | deferred>.
Repo: <worktree-root>/<repo>-<ticket>, your own worktree of <repo-path>. Create it, work only
there, and never touch the main checkout:
  mkdir -p <worktree-root>
  git -C <repo-path> fetch -q origin
  git -C <repo-path> worktree add <worktree-root>/<repo>-<ticket> -b <branch> origin/<default-branch>
  cd <worktree-root>/<repo>-<ticket>
If your shell resets its directory between commands, use absolute paths and `git -C` on the
worktree. Then read that worktree's AGENTS.md and follow it. Commit and push your branch at each
meaningful step so a restart loses nothing.
Goal: <one sentence>.
Skills: <ticket skill, repo skills><, none>.
Data: <"touches <surface>: follow the repo's privacy or data rules" | "no user data surface">.
Authority: <"Merge when CI is green and <review bot> is clean, then deploy as the repo's AGENTS.md
says" | "Do not merge or deploy">. Do not widen scope; report new work you find instead.
Done when: every acceptance criterion is met with its evidence, the PR names <ticket id>, the
ticket is in review<, and every <review bot> round is resolved: each finding fixed or answered,
re-checked after each push>. Then reply in at most three lines: what changed and the evidence
(PR url, checks, review state, evidence links); what remains or what you found outside scope;
any decision needed.
If the ticket is wrong or you are blocked, stop and reply with one paragraph: what is blocked,
what you tried, what decision you need and your recommendation.
```

## 4. Follow Through

- Workers report back when they finish or get blocked; check open PRs (for example with
  `gh pr view`) when you need state in between.
- Answer worker questions from the ticket, repo and docs. Decisions the Authority setting keeps
  with the human go to the human in the escalation format; never guess them. Resume the same
  worker with the answer instead of spawning a new one.
- A worker's "done" is reported, not verified. Mark it verified only after you checked the
  evidence yourself: PR merged or mergeable, checks green, review bot clean, and each acceptance
  item's evidence opens and shows what it claims. Work that needs the human's look is awaiting
  review, not done.
- After merge and verification, close the ticket and remove the worker's worktree
  (`git -C <repo-path> worktree remove <worktree-root>/<repo>-<ticket>`).

## 5. Report

The status board is where the human reads progress and the single source of truth for what they
must know or do. The board gets every update; chat carries only what the Chat rule allows.

- **Board first.** Anything the human needs to know or do is on the board before, or in the same
  step as, any chat mention: an answerable question record on the card it blocks, or on one
  "other" record when no outcome owns it. Chat never carries a need the board lacks. Never
  announce a need as coming ("it will be on the card shortly"): post the question, then mention
  it. If a worker will post it, post it yourself now and let the worker revise that same record.
- **One card per outcome.** Add a need or step to the existing card for its outcome; never create
  a new card or work item for a step that belongs to an existing outcome.
- **Needs the human.** A card needs the human only while it has an open question; derive that
  from open questions, never from free text or a flag. A card whose text says it needs the human
  carries at least one open question.
- **Moves.** When you create, split, merge or move an outcome or work item, move its open
  questions with it and fix any text on the old card that pointed at them.
- **Direction changes.** When a decision changes an outcome's direction (for example a plan is
  replaced), update that card's status text, next step and work items in the same step, and
  resolve or withdraw the questions the decision made obsolete.

- **Outcome linkage.** Every task, deliverable, blocker and decision names its outcome id, or is
  additional work classified as: necessary (needed for an existing outcome; name it), proposed
  scope (new direction; proposed until accepted as Authority says) or deferred (recorded, not
  worked now). Say what each discovery does to the dated commitments.
- **Update format.** `[Outcome]: [current status]. [Meaningful change and evidence].
  [Next step or decision needed].` Evidence is a link (PR, ticket, rendered evidence, deployed
  page); file names, logs, command output and technical detail stay behind links.
- **States.** Keep apart: running, queued, blocked, reported (the worker says done), verified
  (you checked the evidence), awaiting review (needs the human), done. Never show reported work
  as verified.
- **Baseline.** Never rewrite the original commitments to make progress look better. Each change
  to an outcome, date, priority or scope is a change record: date, what changed, reason, who
  decided, impact on commitments.
- **Persist as it happens.** Write each meaningful update to the board when it happens, before
  saying anything in chat. Meaningful: an outcome's status changes, new evidence, a new blocker or
  risk, a discovery, a decision asked or answered. Not: each subtask, push or review round. Daily
  or weekly summaries supplement the board; they never replace it.
- **Escalation.** One record per question, on the card it blocks, with: outcome and work item; the
  concrete question; your recommendation; the real alternatives; what is blocked or at risk and
  the real deadline, if any. An answer, on the board or in chat, is written to that same record,
  then you resume the work and record that you did.
- **Chat.** Chat carries only: answers to what the human asked or told you; a worker or outcome
  that finished and is verified done; something broken or blocked that needs the human, already
  on the board. Each is one line naming the board item. Never send progress notes, merges,
  restarts, resumed workers or other routine updates, never paste the board or post a fresh
  overview.
- **Audit.** Before every report and on every restart or compaction, check that every need you
  told the human about is an open question on the board (none announced as coming), every open
  question sits on the card it blocks, no card has stale "needs you" text, no card or work item
  duplicates a step of an existing outcome, and every card whose direction changed shows the new
  status, next step and work items with obsolete questions resolved. Resolve or withdraw every
  open question whose subject already happened or was decided elsewhere (merged, done, answered in
  chat), and check that the board's needs-the-human count equals the items it lists. Fix gaps
  before saying anything else.

## 6. Restart And Compaction

On every session start, after a context compaction, and whenever a worker report mentions work you
do not remember:

1. Read the status board, then the plan, then the open tickets and PRs in its scope.
2. For each worker row still in flight, check whether its worker is alive. If not, read its
   worktree (`git -C <worktree> status`, unpushed commits) and PR, then resume it or relaunch it
   with its brief plus "continue from <state>". Never start a twin.
3. For every worker that stopped, finished or died, check what it actually delivered (PR, files,
   board records) against each item in its brief, and finish or resume the missing parts. A
   promised board question or other item meant for the human comes first: post it yourself now.
4. Run the Report audit and fix its gaps.
5. Act first on answered questions that no one has acted on yet. Record what you reconciled.

## Safety

- No secrets and no raw personal or customer data in tickets, briefs, comments, the status board
  or reports; summarize and de-identify.
- Repo work happens only in worker worktrees on branches with PRs, never on the default branch.

## Failure Modes

- You edited, committed or pushed in a repo: stop, hand the change to a worker ticket.
- A worker started before its launch approval, or without a ticket.
- You capped, paused or serialized workers instead of coordinating their integration.
- A worker reports done with review findings unanswered or acceptance criteria unmet: send it back.
- You relayed a worker's "done" or "evidence attached" as verified without opening the evidence.
- A blocked worker sits silent: check its PR and output, unblock it or escalate.
- A worker was launched as a new top-level thread or session instead of a subagent.
- State lived only in your context or in a temporary file, and a restart or compaction lost it.
- The baseline was edited instead of recording a change, or added work was mixed into the original
  commitments.
- Routine updates (progress, merges, restarts, resumed workers) went to chat instead of only the
  board.
- You told the human to do or decide something that is not an open question on the board, or a
  card says it needs the human without one.
- Behavior the human asked for lived only in your private memory or harness settings, so another
  agent or harness could not reproduce it.
- You told the human a need would appear on the board soon instead of posting it first.
- A decision changed an outcome's direction but its card kept the old status, next step, work
  items or now-obsolete questions.
- You opened a new card or work item for a step that belongs to an existing outcome's card.
- A worker stopped (finished, died or restarted) before delivering part of its brief, such as a
  board question for the human, and no one compared its output to the brief.
- An open question asked the human for something that had already happened or been decided (a PR
  already merged, a step done, an answer given in chat), or the board's needs-the-human count did
  not match the items it lists.
