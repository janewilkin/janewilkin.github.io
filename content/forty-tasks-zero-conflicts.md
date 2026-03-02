---
title: "Forty Tasks, Zero Conflicts: What I Rebuilt When Concurrency Broke the Backlog"
date: March 2026
reading_time: 12 min read
description: >-
  The flat markdown backlog worked beautifully until six agents started
  shipping in parallel. Per-task files, tiered CI, and a merge queue
  turned constant merge conflicts into smooth concurrent development.
---

At the end of my second article, I thought I knew where the bottleneck was heading next. I'd solved coordination with claim locks, worktrees, and a shipping pipeline. I'd built a planning system with eight specialized perspectives that could see the shape of the work. What I planned to tackle next, I wrote, was counsel: encoding wisdom so that agents could consult it.

I was wrong about the sequence.

Before I could get to counsel, the infrastructure I'd celebrated in my first article started breaking. Not the coordination tooling. The claims, the locks, the version speculation all held up. What broke was simpler and more fundamental: the flat markdown file.

## The Flat File's Limit

The project is a policy research platform that tracks legislation, organizational stances, and media coverage across jurisdictions, currently deploying to a QA environment. NEXT-STEPS.md was the centerpiece of the workflow I described in my first two articles. Every task lived in a single file. The leader review system populated it. The claim system read from it. The `/ship` pipeline updated it. I built the entire planning and coordination apparatus around the assumption that one file could serve as the shared truth for the project's backlog.

The second article even noted: the flat file worked, and I'd migrate the moment it stopped.

And it worked. For one agent, or two, or even three working on tasks spread far enough apart in time that their pull requests didn't overlap.

The problem surfaced when I started running six agents concurrently as a regular practice. Each agent works in its own git worktree, on its own branch, implementing its own task. When the agent finishes and ships via `/ship`, the pull request includes changes to NEXT-STEPS.md: the completed task gets checked off, context notes get updated, sometimes new tasks get added. I wanted the tracking update atomic with the code change -- if a PR reverts, the task status reverts with it. A post-merge hook could have avoided the contention, but at the cost of the backlog sometimes disagreeing with the codebase. So the tracking and the implementation shipped together, and six agents meant six pull requests all touching the same file.

Git can auto-merge changes to the same file when they touch different lines. But six agents modifying scattered locations in a several-thousand-line markdown file is exactly the kind of change pattern that produces merge conflicts. Not because the changes are related. They're completely independent. An agent finishing a security hardening task has nothing to do with an agent finishing a navigation redesign. But both mark their task as done in the same file, and if their PRs land close enough together, the second one conflicts.

In a typical six-agent session, I'd hit three or four merge conflicts on NEXT-STEPS.md, each taking five to ten minutes to untangle. The coordination infrastructure that eliminated conflicts in source code was generating them in the backlog file.

## One Task, One File

The fix is one of the oldest patterns in concurrent systems: reduce contention by eliminating shared mutable state. If multiple agents need to modify the backlog without conflicting, don't store the backlog in a single file.

I split NEXT-STEPS.md into individual task files. Each task is a standalone markdown file in `next-steps/active/`. When an agent completes a task, the file moves to `next-steps/completed/`. The directory structure looks like this:

```
next-steps/
├── _meta.md
├── _sections.toml
├── active/
│   ├── add-geographic-tagging-to-articlerecord.md
│   ├── build-model-bill-propagation-tracker.md
│   ├── fix-organization-stance-display.md
│   └── ... (40 files)
└── completed/
    ├── add-stance-aware-integrity-checks.md
    ├── build-data-integrity-validator.md
    └── ... (98 files)
```

The task names hint at the scope: geographic tagging for legislative records, model bill propagation tracking across jurisdictions, integrity checks that cross-reference organizational stances against voting records. Each one is a self-contained unit of work.

The `_sections.toml` file defines the grouping structure: section IDs, titles, priorities, sort order, and descriptions. This is the metadata that used to be implicit in the markdown heading hierarchy. Making it explicit means the structure is defined once and applied consistently whenever the flat file is regenerated.

NEXT-STEPS.md still exists. It's now a generated artifact. A Python script, `task-format.py render`, reads all the task files, groups them by section, sorts them by priority, and produces the same human-readable markdown document that existed before. The flat file went from being the source of truth to being a view over the source of truth.

The result: when an agent ships, its pull request touches only the specific task file it completed and the source files it changed. Two agents shipping simultaneously modify completely different files. Merge conflicts on the backlog dropped to zero. Agents can still conflict on shared source files -- a utility module, a configuration file -- but the claim system reduces that surface area by ensuring agents work on different tasks, and the backlog itself is no longer a bottleneck.

This is not a novel design. It's the same principle behind maildir versus mbox, or per-record database rows versus a flat table. When concurrent writers contend on a shared resource, split the resource into independent units. The pattern is decades old. I just needed the concurrency pressure to force me into applying it.

## Fast Feedback, Rigorous Validation

Eliminating merge conflicts was half the cycle time problem. The other half was CI.

With one or two agents, the test suite ran once per PR and the wait was acceptable. With six agents shipping within the same hour, the CI pipeline became a queue. Each pull request triggered the full test suite -- over 3,600 tests across 116 test files, plus linting, plus type checking. Even with parallel test execution, the suite takes a few minutes. Multiply that by six concurrent PRs and add the serial nature of merge validation, and the wall-clock time from "agent finishes implementation" to "code lands on main" stretched to the point where it was undermining the concurrency gains.

The solution was tiered testing. Pull request checks run a fast subset:

```yaml
- name: Run tests (fast)
  if: github.event_name == 'pull_request'
  run: |
    pytest -n auto -q --no-cov -m "not slow and not browser and not ci_only"
```

This skips slow tests, browser tests, and tests marked as CI-only, and it skips coverage calculation. The fast suite gives the agent quick feedback: did the implementation break anything obvious? If so, the agent can fix it immediately without waiting for the full run.

The merge queue runs the comprehensive suite:

```yaml
- name: Run tests with coverage
  if: github.event_name != 'pull_request'
  run: |
    pytest -n auto --cov --cov-report=term-missing -q
```

This is the full battery: every test, with coverage enforcement. Nothing reaches main without passing it.

The split gives agents fast feedback on obvious breakage -- seconds, not minutes -- while the merge queue catches the rest: cross-cutting failures, coverage regressions, slow integration tests that don't belong in a PR check.

## The Merge Queue

The merge queue is the piece that ties everything together. Without it, the tiered testing would have a gap: PRs pass their fast checks, merge into main, and if two PRs interact badly, the failure shows up after the fact. With the merge queue, each PR is validated not just against the current main branch but against main plus every PR ahead of it in the queue. Interaction failures get caught before they reach main, not after.

I upgraded to GitHub Enterprise for its merge queue support -- private repos on lower tiers don't have access. Tools like Mergify and Bors solve the same problem without the tier upgrade. When six agents can each produce a shippable PR in under an hour, the merge queue is what keeps main green without slowing them down.

The `/ship` skill and CI workflow were built for the merge queue before Enterprise was activated -- agents would error on the queue commands and fall back to direct merge until the upgrade went through. When `mergeQueue` is enabled in the project's configuration, the skill adds the PR to the queue instead of merging directly:

```json
{
  "mergeMethod": "squash",
  "mergeQueue": true
}
```

From the agent's perspective, nothing changed. It runs `/ship`, the PR gets created, and the skill handles the rest. The agent doesn't know or care that its PR is being validated against three other PRs in the queue. It ships and moves on to the next task.

When the merge queue does reject a PR -- usually a test that passes in isolation but fails against other queued changes -- the PR drops out of the queue and I get a failure notification. This happened two or three times in the first week: a shared constant that two tasks both modified, a test that assumed insertion order. Each time, the fix was straightforward. The merge queue caught the interaction before it reached main, which was the point.

## The Compound Effect

Per-task files, tiered CI, and merge queues are all well-known patterns. What made the difference was applying them together to one specific problem: reducing the wall time between "agent finishes work" and "code lands on main" when multiple agents are working concurrently.

Before these changes, the cycle looked like this: agent finishes, creates PR, waits for full CI, PR merges, next agent's PR has a merge conflict on NEXT-STEPS.md, someone resolves the conflict, CI reruns, PR merges, and by then a third agent's PR has also conflicted. The serial dependency chain turned parallel agent work into sequential merge resolution.

After: agent finishes, creates PR, fast CI validates in seconds, PR enters the merge queue, full CI validates in the queue, PR lands on main. Meanwhile, five other agents are doing the same thing. Their PRs touch different task files and different source files. No conflicts. The queue serializes the merges, but the testing and development happen concurrently.

The first session with these changes was the first one where I didn't step in to resolve a conflict. Each PR is scoped to a single task, so reviews focus on whether the implementation matches the task intent, whether the test coverage is meaningful, and whether the change introduces architectural drift. With the merge mechanics automated, that review is where I spend my time.

## Taking It Forward

I built all of this for one project with one specific set of pressures. I think the patterns generalize, but I've only validated them here so far.

The per-task file architecture should scale linearly with concurrency: adding a seventh or eighth agent adds no contention because each agent's changes are already isolated by design. The tiered CI split between "fast feedback" and "rigorous validation" applies anywhere the test suite is large enough to create meaningful PR latency. And the merge queue pays for itself the moment you have more than two sources of concurrent changes.

I've started backporting these patterns into the [Claude project template](https://github.com/janewilkin/claude-project-template) -- the per-task file architecture, the task-format.py script, the tiered CI configuration. Whether they hold up on a different project with different pressures is the next test.

This is the third article in what has become a series about bottleneck migration. The constraint has moved three times -- from implementation to coordination, from coordination to planning, from planning to cycle time -- and each fix revealed the next.

The Theory of Constraints describes this progression. At TIBCO, I watched it play out over two years across a 40-60 person operations group: automating deployments revealed that cross-team communication was the real bottleneck. Building shared runbooks and running workshops across teams addressed that, and then the constraint was institutional knowledge -- critical procedures that lived in three people's heads.

The same progression is happening here, compressed from years to weeks. I can identify a constraint, build a fix, and hit the next one in a single working session. The problems themselves -- concurrency, contention, the gap between parallel work and serial integration -- are the same ones that come up in any system where multiple contributors need to ship to the same codebase. Agents compressed the timeline. The problems are familiar.

---

*This article was drafted with AI assistance and reviewed for factual accuracy.*

*If you're interested in working together, reach out at [jane@janewilkin.dev](mailto:jane@janewilkin.dev).*
