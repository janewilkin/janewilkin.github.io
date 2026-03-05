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

The engineering team had a strong attachment to the database layer. Years of a "golden screwdriver" approach -- building things manually, pushing straight to production on completion -- had created a culture of direct ownership. The database was MySQL 5.5.40, self-managed on EC2, sitting underneath a platform that handled over a billion API calls a month, with a multi-tiered replication topology. It had been running since the service launched around 2012. There were known problems that people agreed upon, but changing the status quo meant changing how people thought about the system.

My immediate manager and I, both on the operations team, agreed that moving to a managed MySQL solution on AWS was a priority. We were the ones feeling the pain of all the TOIL related to not just the write master, but the entire replication topology. EC2's SLA at the time gave no guarantee that specific instances could run forever, uninterrupted. We were already plagued by frequent automatically scheduled maintenance events on other instances. The write master had simply been lucky. And in an organization with a 99.99% SLA commitment, that luck was doing the heavy lifting.

I understood the reluctance to take on a migration at that scale. A failed migration doesn't just mean a bad day. It means broken trust with customers, an SLA violation that shows up in quarterly reviews, and the kind of incident that follows you into every planning meeting for the next year. The version was nearly end-of-life and at risk of causing a compliance breach. The operational burden of managing MySQL ourselves was real, even if it had become invisible because we'd gotten so good at absorbing it. That burden was made of every incident response, manual failover, or late-night page that could have been avoided with a managed service. All of that toil was weighing heavily on a team already spread thin, and replication lag was becoming a consistent issue over time, as more databases were added one at a time without a full review of the topology.

The real risk was the sword of Damocles hanging over us. If the write master instance or an attached EBS volume were to fail, it would have caused a major outage that could have seriously hurt customer trust in the business. We needed to communicate both the ongoing burden of owning the MySQL application and doing undifferentiated labor to tune it, and the catastrophic risk we were carrying every day.

So I started making the case.

## The Foundation I Inherited

I wasn't starting from nothing. When I joined the team, we were in the middle of an internal rebranding from operations to Site Reliability Engineers, focusing on the principles from Google's SRE handbook. About a year before I joined, two engineers had done serious, careful work migrating the database instances from EC2 instance store to EBS-backed volumes. There had never been a migration of the write master before that. The risk was high because a lack of architectural rigor in parts of the system meant stakeholders couldn't be certain there wasn't a service out there connecting to the write master with a hard-coded IP address rather than a domain name. That seemed impossible to have been left undone, but in some ways it wasn't a surprising symptom of a system built under the intense pressure of a 2012-era startup. Mashery eventually became "API Management" under TIBCO, until it was sold to Boomi. Part of the work ahead of the first migration I handled was to introduce a domain name for the write master.

The key technical challenge was logical, not mechanical. You had to stop writes at the application layer for multiple different worker types. Then stop writes at the MySQL layer. Confirm all changes had replicated to the next master. Then re-enable writes as quickly as possible to serve as few errors as possible. Every step depended on the one before it, and speed mattered.

They had built documentation, written scripts, and established a procedure that worked. When I inherited that body of work, I could read the logic in the scripts and see the thinking behind it. The rigor was evident.

These were colleagues I hold in high regard. We shared a set of values that isn't universal in operations: do things right, make them repeatable, specify them in code. I came into the operations team from a software development and engineering background, and finding people who thought the same way about infrastructure work was a gift. Their prior migration gave me a foundation to build on. It also gave me confidence that the organization could do this kind of work well, because it already had.

What I was proposing was bigger in scope. Moving to a completely different database engine, not just changing the underlying storage. The discipline those engineers had brought to their migration gave me the order of operations and the mechanisms for disabling writes that I built on for mine.

## The Hard Part

The technical work was hard. Designing the migration procedure, testing it, building the rollback plan for a platform at this scale against a 99.99% SLA. That was real engineering. The path forward was at least legible. AWS had good documentation. Aurora Global was a mature product. I could see the steps, even if each one carried risk.

The harder problem was changing the mental model. People felt "safe" with a risky EC2 instance that just happened to keep working. The real shift was getting the team to recognize that we were already in an unsafe situation, and that moving to Aurora was moving toward greater safety, not away from it.

I had to make the argument to engineers who believed that maintaining direct control of MySQL was an uptime advantage, to managers who had to balance many competing priorities, and to stakeholders who were far enough away from the problem to not hear about the related issues it was causing as part of their typical work day. With management, I had to frame it in terms of operational cost and risk trajectory. With stakeholders, I had to make the invisible costs visible. All of this communication, coordination, and consensus building is perhaps not typically thought of as system architecture work, but experienced professionals know that it's not just the code or the platform that makes a system work, it's rich discussion and coordination around the system, which is of course based in human language.

## The Migration

Two years into my time on the team, we were ready. I had written and tested the procedure and the tools. I had hands on keyboard for stopping writes at the master, confirming completion of replication, setting and removing maintenance mode. Another SRE assisted with updates to the write master domain name and reviewed lingering network connections. Our manager was on the call helping coordinate with engineering and management, but I was leading the process.

The procedure worked. The rollback plan sat unused. The SLA held. We had minimal downtime, and the platform came up on Aurora Global without incident.

Gradually, seconds feeling like hours, the successful status codes and the focused, tense, methodical verifications confirmed that we were in the clear. The collective sigh of relief was palpable. Nothing broke. The best possible outcome was a quiet success.

## The Pay off

I learned about stewardship early, during eight years building trading systems at Fidessa. I watched client systems that had been heavily and independently customized by distinct onsite teams get brought into parity through enhancements, feature flags, and documentation created for every change. The systems that had been aligned into a common base were upgraded and iterated on more quickly than those that continued with fully bespoke implementations. That lesson stayed with me. By the time I was leading this migration, I already knew that the procedure itself was only half the job. The other half was making sure anyone could pick it up, understand the reasoning, and run it themselves.

So we documented everything: discussion and decision-making process, testing methodology, performance metrics, runbooks, and playbooks. Every step was specified so that the procedure didn't live solely in anyone's head.

The migration procedure we'd built was solid enough that we used it again, and again. Over the following years, we ran the same fundamental approach three more times for version upgrades, each time without incident. A process that started as a one-time, high-stakes operation became a repeatable capability. The technical design of the migration mattered, but it was the trust we'd built that gave the team confidence that it could be done safely again.

Over the course of my career I realized that there's so much beyond writing code that makes systems work, and rather than make myself gatekeeper or a single point of failure by keeping institutional knowledge to myself, empowering others and setting them up for success through knowledge sharing in the form of documentation, collaboration, and mentorship.

---

*If you're interested in working together, reach out at [jane@janewilkin.dev](mailto:jane@janewilkin.dev).*
