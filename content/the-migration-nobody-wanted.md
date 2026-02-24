---
title: Leading the Migration Everyone Depended On
date: February 2026
reading_time: 8 min read
description: >-
  How I built the case for migrating a legacy MySQL database to Aurora Global
  on a platform handling over a billion API calls a month.
---

*This article was originally published on
[LinkedIn](https://www.linkedin.com/pulse/migration-nobody-wanted-jane-wilkin-hmmhe/).*

Nobody wanted to touch the database.

It was MySQL 5.5.40, self-managed on EC2, sitting underneath a platform that handled over a billion API calls a month. It had been running since the service launched in 2014. It worked. Not elegantly, not safely, but it worked. EC2's SLA at the time gave no guarantee that specific instances could run forever, uninterrupted. We were already plagued by frequent automatically scheduled maintenance events on other instances. The write master had simply been lucky. And in an organization with a 99.99% SLA commitment, "it works" is a powerful argument for leaving something alone, even when you know that luck is doing the heavy lifting.

I understood the reluctance. Every SRE on the team knew the risks. A failed migration at that scale doesn't just mean a bad day. It means broken trust with customers, an SLA violation that shows up in quarterly reviews, and the kind of incident that follows you into every planning meeting for the next year. The rational move, from almost every angle, was to keep patching it and hope nothing went wrong.

But it felt like a sword hanging over us, and I kept coming back to what would happen if we didn't move. The version was aging out of support. The operational burden of managing it ourselves was real, even if it had become invisible because we'd gotten so good at absorbing it. That burden was made of every incident response, manual failover, or late-night page that could have been avoided with a managed service. All of that toil was weighing heavily on a team already spread thin, and the system was starting to show cracks. Replication lag was growing steadily, demanding more and more SRE time and attention just to understand why, let alone fix.

So I started making the case.

## The Foundation I Inherited

I wasn't starting from nothing. About a year before I joined, two engineers had done serious, careful work migrating the database instances from EC2 instance store to EBS-backed volumes. There had never been a migration of the write master before that. The risk was high because a lack of architectural rigor in parts of the system meant stakeholders couldn't be certain there wasn't a service out there connecting to the write master with a hard-coded IP address while others used a domain name. The key technical challenge was logical, not mechanical. You had to stop writes on the current master. Confirm all changes had replicated to the next master. Stop writes at the application layer for multiple different worker types. Then re-enable writes as quickly as possible to serve as few errors as possible. Every step depended on the one before it, and speed mattered.

They had built documentation, written scripts, and established a procedure that worked. When I inherited that body of work, I could read the logic in the scripts and see the thinking behind it. The rigor was evident.

These were colleagues I hold in high regard. We shared a set of values that isn't universal in operations: do things right, make them repeatable, specify them in code. I came into the operations team from a software development and engineering background, and finding people who thought the same way about infrastructure work was a gift. Their prior migration gave me a foundation to build on. It also gave me confidence that the organization could do this kind of work well, because it already had.

What I was proposing was bigger in scope. Moving to a completely different database engine, not just changing the underlying storage. But the discipline those engineers had brought to their migration informed everything about how I approached mine.

## The Hard Part

The technical work was hard. Designing the migration procedure, testing it, building the rollback plan for a platform at this scale against a 99.99% SLA. That was real engineering. But the path forward was at least legible. AWS had good documentation. Aurora Global was a mature product. I could see the steps, even if each one carried risk.

The harder problem was convincing people it was worth that risk.

I had to make the argument to engineers who had been burned before by ambitious infrastructure changes. To managers who were measured on uptime and didn't want to introduce unnecessary risk to their numbers. To stakeholders who didn't understand why something that "worked fine" needed to change. Each of these conversations required a different kind of approach. With the engineers, I had to be specific about the procedure, the rollback strategy, the blast radius. With management, I had to frame it in terms of operational cost and risk trajectory. With stakeholders, I had to make the invisible costs visible.

None of this was coding. All of it was necessary.

## The Migration

Two years into my time on the team, we were ready. I had written and tested the procedure and the tools. I had hands on keyboard for stopping writes at the master, confirming completion of replication, setting and removing maintenance mode. Another SRE assisted with updates to the write master domain name and reviewed lingering network connections. Our manager was on the call helping coordinate with engineering and management, but I was leading the process.

The procedure worked. The rollback plan sat unused. The SLA held. We had minimal downtime, and the platform came up on Aurora Global without incident.

Gradually, seconds feeling like hours, the successful status codes and the focused, tense, methodical verifications confirmed that we were in the clear. The collective sigh of relief was palpable. Nothing broke. The best possible outcome was a quiet success.

## The Payoff

That instinct to document everything came from somewhere. I learned about stewardship early, during eight years building trading systems at Fidessa. I watched client systems that had been heavily and independently customized by distinct onsite teams get brought into parity through enhancements, feature flags, and documentation created for every change. The systems that had been aligned into a common base were upgraded and iterated on more quickly than those that continued with fully bespoke implementations. That lesson stayed with me. By the time I was leading this migration, I already knew that the procedure itself was only half the job. The other half was making sure anyone could pick it up, understand the reasoning, and run it themselves.

So we documented everything: discussion and decision-making process, testing methodology, performance metrics, runbooks, and playbooks. The scripts and their rationale. Every step was specified so that the procedure didn't live solely in anyone's head.

The migration procedure we'd built was solid enough that we used it again. And again. Over the following years, we ran the same fundamental approach three more times for version upgrades, each time without incident. A process that started as a one-time, high-stakes operation became a repeatable capability.

The technical design of the migration mattered. But what made it repeatable wasn't just the technical design. It was the trust we'd built during the first one. The engineers who'd been skeptical now had evidence. The managers who'd worried about their SLA numbers had data. The next migration didn't require months of advocacy because the first one had created organizational confidence.

I'd spent most of my career thinking of myself as a coder. Someone who writes software, understands systems, solves technical problems. And I do those things. But the work that made the biggest difference here wasn't writing code. It was seeing what the organization had learned to live with, building the case for changing it, and documenting it well enough that I didn't need to be in the room next time.

The fourth migration went smoothly and nobody thought twice about it. That's the result I'm most proud of.
