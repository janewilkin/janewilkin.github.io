---
title: The Bottleneck Moved
date: February 2026
reading_time: 18 min read
description: >-
  When Claude Code handles implementation, the bottleneck moves to coordination.
  How I built a sharable template for managing multiple AI agents, drawing on
  patterns from human software teams.
---

Three weeks into using Claude Code full-time, I stopped writing code.

Not entirely. But the balance shifted in a way I didn't expect. I was generating working implementations faster than I could decide what to build next. The code was fine. But I'd spend twenty minutes specifying something, Claude would produce it in seconds, and then I'd sit there looking at five other things that also needed specifying. The bottleneck had moved from implementation to planning, prioritization, and coordination.

This is happening to a lot of people right now.

Wes McKinney, the creator of pandas and co-creator of Apache Arrow, [recently described a version of this shift](https://wesmckinney.com/blog/mythical-agent-month/). He's been building projects in Go, a language he wasn't previously proficient in, because AI agents made language fluency less important than fast feedback loops. His point isn't really about Go. It's that when agents handle the typing, what matters is how quickly you can validate their output and how well you can organize the work. The skills that become critical are architectural thinking, specification, and coordination.

I see a wide spectrum across the industry right now. Some engineers aren't permitted to use AI tools at work. Others are going all in, publicly explaining how they're building entire projects with Claude. Most of us are somewhere in between, figuring out how to integrate these tools without losing the things that made us good at our jobs in the first place.

## Protecting the Exploratory Part

For me, the thing I didn't want to lose was the exploratory part. The sessions where you spend an afternoon tracing through a system, building a mental model, understanding why something works the way it does. That's the part of the work I've always been drawn to most. When I first started using Claude Code, I felt protective of it. I worried that delegating implementation would shortcut the understanding.

So rather than using Claude at work, where I might feel pressured to move fast and skip the learning, I started using it extensively in personal projects. I gave myself permission to explore at my own pace, to figure out where the tool helped and where it got in the way, to develop my own workflow before anyone else's expectations shaped it.

What I found was that the understanding didn't disappear. I wasn't tracing through code to figure out how to implement something. I was thinking about how the work should be organized, what depends on what, and how to express intent clearly enough that another entity could act on it.

And once I got comfortable with that shift, I hit the next wall: I could get Claude to implement things simultaneously, but I needed to coordinate the work of multiple Claude agents. That's when the real problem got interesting.

## The Coordination Problem

On a typical session I run four to six Claude Code agents in parallel, each in its own git worktree. And I immediately ran into the same problems that software teams run into. Two agents picking up the same task. Version conflicts when both try to ship. Changes landing in the main branch while another agent is mid-flight on something that depends on the old state. The familiar challenges of concurrent development, compressed from days into minutes.

I've heard people argue that the right way to organize sub-agents is by the amount of context needed to perform a task. That's true operationally. Context window management is a real constraint, and you do need to think carefully about what information each agent needs. But the reason we organize human teams the way we do isn't arbitrary. We've iterated on team structures across thousands of organizations over decades. Feature branches, code ownership areas, work queues, pull request reviews, CI gates. These patterns exist because coordinating parallel work on shared systems is hard, and we've had time to develop good solutions.

Using those same patterns for multi-agent workflows isn't nostalgia. It's recognizing that the coordination problems are the same even when the workers are different.

I could have reached for an external coordination system: a project board, a task manager, a purpose-built orchestration framework. But I wanted to explore how well Claude could solve this problem itself, just by asking it to build the coordination tooling. So I started prompting Claude to help me build a template that codifies these patterns for Claude Code projects.

## The Template

What I've been iterating on is a [Claude project template](https://github.com/janewilkin/claude-project-template): a reusable configuration that you can drop into any Python project and immediately get a structured development environment for working with Claude Code. It's open source.

The template addresses three problems I kept running into:

1. Starting every project by re-configuring permissions, linting hooks, and review workflows from scratch
2. Coordinating multiple Claude Code agents working on the same codebase
3. Keeping configurations consistent across projects as I learned what worked and improved the setup

What follows is a walkthrough of how the pieces fit together.

## Project Context

At the foundation is CLAUDE.md, a file that sits in the project root and gives Claude the context it needs: what the project does, how it's structured, what conventions to follow, what skills are available. You can think of it as the equivalent of onboarding documentation for a new team member, except the team member reads it every single time it starts a session.

The quality of this file matters more than you'd expect. A vague CLAUDE.md produces vague work. A specific one that describes architecture, naming conventions, testing requirements, and code style produces implementations that fit naturally into the existing codebase. The template ships a structured CLAUDE.md that you fill in for your project, with sections for architecture, commands, conventions, and available skills.

## Permissions: Safety Without Friction

Claude Code's permission system asks you to approve tool usage. That's the right default. But if you're approving "yes, you can run pytest" fifty times a day, the safety model becomes friction that degrades your workflow without meaningfully improving security.

The template ships with about eighty allow rules and a handful of deny rules. Many of the allow rules are variant invocations of the same tools (pytest can be called four different ways), but the design principle is simple: draw a clear line between safe operations and dangerous ones.

```
{
  "allow": [
    "Edit(**.py)",
    "Bash(pytest *)",
    "Bash(ruff check *)",
    "Bash(git add *)",
    "Bash(git commit *)",
    "Bash(gh pr *)",
    "WebFetch(domain:docs.python.org)"
  ],
  "deny": [
    "Read(.env)",
    "Read(**/*credentials*)",
    "Read(**/*.pem)",
    "Bash(rm -rf *)",
    "Bash(sudo *)",
    "Bash(curl * | *)"
  ]
}
```

The allow list covers the operations you perform constantly: editing Python files, running tests and linters, git operations, fetching documentation. The deny list blocks the things that are actually dangerous: reading secrets, destructive filesystem operations, piping untrusted remote content to a shell. Notably, `curl * | *` is denied because fetching arbitrary URLs and piping the result to bash is a well-known attack vector, but regular `curl` commands are permitted.

The result is that Claude can work through a normal development session without interrupting you for permission, but it still can't read your credentials or delete your project.

## Skills: Specialized Capabilities

Claude Code supports "skills," which are markdown files that define specialized capabilities. You invoke them with slash commands like `/lint` or `/test` or `/ship`. Each skill is a self-contained instruction set with its own version, description, and explicit list of tools it's allowed to use.

Here's the frontmatter from the `/ship` skill, which handles the complete workflow of committing, versioning, creating a PR, merging, and syncing the local repository:

```
---
name: ship
version: 1.2.0
description: >
  Commits changes, creates a PR, merges it, and syncs
  the local repo. Complete workflow from worktree changes
  to running code in one command.
argument-hint: "[commit message or empty for auto-generated]"
allowed-tools: Read, Glob, Grep, Edit, Bash(git *),
  Bash(gh *), Bash(ruff *), Bash(mypy *), Skill
---
```

The template includes 19 skills. Some are straightforward development tools: `/lint`, `/test`, `/review`, `/docs`. Some are workflow automation: `/ship`, `/version`, `/check` (which runs the full validation pipeline of lint, test, review, docs, and bash-review in sequence). Some are more unusual: `/comic` generates SVG explainer comics about the project, `/cost-estimate` analyzes API spending, and `/prompt-review` grades every AI prompt in the source code and suggests improvements.

But the skills I want to focus on are the ones that solve the coordination problem.

## The Work Queue

When multiple Claude Code agents work on the same project, they need a way to divide the work without duplication. The template includes a work queue system built on a simple idea: file-based claim locks in a shared directory.

Every Claude Code project can use git worktrees for isolation. A worktree is a lightweight copy of your repository on its own branch. The agent works in its worktree, and when it's done, the changes merge back to main via a pull request. This is how the template handles the "don't step on each other's code" problem.

The claim system handles the "don't pick up the same task" problem. When an agent claims a task, it writes a JSON file to a shared directory that all worktrees can see:

```
{
  "task_slug": "fix-config-validation",
  "task_title": "[steward] Fix config validation edge case",
  "section": "High Priority",
  "role_tag": "steward",
  "agent_worktree": "festive-mendel",
  "claimed_at": "2026-02-23T14:23:32Z",
  "ttl_minutes": 120,
  "speculated_version": "0.18.0"
}
```

Before claiming a task, the agent checks for existing claims. If another worktree already owns that task, the agent moves on to the next unclaimed item. Claims have a TTL (time to live) of 120 minutes by default, so if an agent crashes or gets abandoned, its claims expire and other agents can pick the work back up.

The `speculated_version` field is worth explaining. When two agents are working in parallel and both need to bump the project version when they ship, they'd naturally both pick the same next version number. The claim system avoids this by having each agent check the highest speculated version across all active claims and increment from there. It's advisory, not enforced. The actual version is determined at ship time. But it prevents the common collision where two agents both target version 0.18.0.

There are other safeguards that I added after running into real problems. The script canonicalizes task slugs from titles to prevent mismatches. It detects duplicate titles across different slugs. It checks open pull requests to find tasks that are already being shipped by another agent, even though they still appear uncompleted in the local task list. And it has a `validate` command that runs a health check across all claims, catching orphaned worktrees, expired claims, and inconsistencies.

All of this lives in a single bash script, `scripts/work-queue.sh`, that handles claiming, releasing, listing, expiring, and validating. It runs from any worktree because it resolves the main repo path automatically.

## The Claim-to-Ship Pipeline

The full workflow ties the pieces together. It starts with `/claim-tasks`, which reads a NEXT-STEPS.md file (the project's task list), filters out completed and already-claimed work, and claims a batch of unclaimed tasks. If you're on the main branch, it automatically creates a fresh worktree first.

Then you (or the agent) work on the claimed tasks. Auto-linting runs after every file edit via a hook. The work is isolated in the worktree's branch.

When you're done, `/ship` handles everything: it stages and commits the changes, runs CI parity checks (the same linting and type-checking that CI runs, so you catch problems before pushing), bumps the semantic version, pushes the branch and tags, creates a pull request, waits for CI to pass, squash-merges into main, syncs the local repository, releases the work queue claims, and offers to clean up the worktree.

The output looks like this:

```
═════════════════════════════════════════════
              SHIPPING CHANGES
═════════════════════════════════════════════

Branch: festive-mendel → main

CI PARITY
  ✓ ruff format clean
  ✓ ruff check clean
  ✓ mypy clean

COMMIT
  ✓ Staged 5 files
  ✓ Committed: "Fix config validation edge case"

VERSION
  ✓ Analyzed commits → MINOR increment
  ✓ Bumped version: 0.17.1 → 0.18.0
  ✓ Created tag: v0.18.0

PULL REQUEST
  ✓ Created PR #42
  ✓ CI checks passed
  ✓ Squash merged into main

SYNC LOCAL
  ✓ Pulled into /Users/jwilkin/code/project
  ✓ Local repo now at: abc1234

═════════════════════════════════════════════
                  SHIPPED!
═════════════════════════════════════════════
```

It's also smart about saving time. If a commit only touches markdown files, Claude config, or documentation, the skill detects this, adds `[skip ci]` to the commit message, and merges with `--admin` to bypass CI checks that have nothing to validate. This sounds small, but when you're shipping frequently, those saved CI minutes add up.

## Staying in Sync

I have several projects that all use this template. As I improve the template (adding new skills, tightening permissions, fixing edge cases), those improvements need to propagate. Rather than manually checking each project, the template includes a `/sync-config` skill that compares the current project's configuration against the latest template and generates a report showing what's changed.

It checks permissions (new allow or deny rules), hooks (new or updated scripts), skills (new skills, version mismatches), and Python tooling (ruff rules, pytest and mypy settings). The report classifies each difference and offers to apply updates selectively.

The fetch mechanism is deliberately resilient. It tries four authentication strategies in order: the `gh` CLI, git clone with an environment token, git clone with credential helpers, and GitHub API calls with curl. This means it works in local development, CI pipelines, cloud IDEs, and GitHub Codespaces. For private templates, at least one auth method needs to be configured, and the error message explains exactly how to set each one up.

## What I Learned Building This

The template has been through about six minor versions in a few weeks. Each version came from hitting a real problem. The work queue safeguards (slug canonicalization, duplicate detection, orphan cleanup) exist because I watched agents claim the wrong tasks and ship conflicting versions. The docs-only detection in `/ship` exists because I got tired of waiting for CI on README changes. The layered worktree detection exists because an agent running from the main repo directory misidentified itself as "main" and tried to release another agent's claims.

Every guardrail in the system came from a real failure mode. That's the same pattern I've seen in every operations system I've worked on. Experienced engineers do design for failures they haven't encountered yet -- but only when they recognize the class of failure from previous systems. Slug canonicalization, claim expiry, orphan detection: these aren't novel ideas. They're the same guards I'd have built into any distributed coordination system, because I've watched the equivalent problems play out in production environments over twenty years. What surprised me was the compression. Failure modes that would take a human team weeks to surface showed up in my first afternoon of running parallel agents.

The other thing I learned is that the skills and configuration files are doing something similar to what CLAUDE.md does for project context: they're compressing institutional knowledge into a format that an agent can consistently act on. When I write a skill definition, I'm encoding a process that I would otherwise have to explain from scratch every session. The `/ship` skill isn't just automation. It's a specification of how we ship code in this project, captured precisely enough that it works the same way every time.

## Where It Gets Hard

The part I haven't solved well yet is visibility. Each agent works from a NEXT-STEPS.md file that lists what needs doing. The agents can generate next steps too, which is useful for keeping momentum, but it creates a new problem: the project's trajectory starts to drift unless I'm reviewing the queue regularly. I came back from a break once to find that three agents had each added next steps around error handling edge cases, and the queue had quietly shifted from feature work to hardening work that wasn't what I needed yet. With four to six agents shipping changes, the project can move fast in a direction I didn't intend if I'm not paying attention to what they're adding to the backlog.

I have skills like `/docs` that I run every few iterations to make sure the documentation stays current with the code. But the bigger question, "where is this project actually heading?", is harder to answer from a flat markdown file. I can see the next steps. I can't easily see the shape of the work. That's the bottleneck I'm hitting now: not coordination of agents, but visualization of progress and trajectory. I suspect this is the kind of problem that will eventually be solved by better tooling, but right now it's a manual review process.

There are other rough edges. The work queue is a bash script, not a database, so it doesn't handle truly concurrent writes gracefully. The version speculation is advisory and can still collide in edge cases. The claim system assumes agents are honest about their identity, which works when you control all the agents but wouldn't survive an adversarial environment. These are acceptable tradeoffs for personal projects, but they're worth naming.

## The New Dotfiles

I think we're at the beginning of something that mirrors what happened with dotfiles in the developer community. For years, developers have shared and compared their shell configurations, their vim setups, their tmux configs. Dotfile repositories on GitHub became a way of expressing how you work, not just what you work on. They spread good practices as people borrowed and adapted each other's setups.

I'm starting to see the same thing happen with Claude Code configurations. People sharing their CLAUDE.md files, their permission rules, their skill definitions. Comparing approaches to agent coordination. Borrowing each other's hooks and workflows. The `.claude/` directory is becoming the new `~/.config/`: the place where you encode your development process.

The template I've been building is my contribution to that conversation. It's opinionated, it reflects the way I work, and it will keep evolving as I learn more. If you're working with Claude Code and thinking about multi-agent workflows, the [repository is public](https://github.com/janewilkin/claude-project-template) and I'd be curious to hear what patterns you've found.

Last week I watched an agent misidentify its own worktree, try to release another agent's claims, and fail gracefully because of a guard I'd added two days earlier. I didn't write that guard because I anticipated the problem. I wrote it because I'd seen the same class of failure before, in a different system, with human operators. Twenty years of watching things go wrong in production turns out to be useful preparation for watching things go wrong with agents. The tools changed. The failure modes didn't.
