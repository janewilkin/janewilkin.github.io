# LinkedIn Post: The Bottleneck Moved

**Status:** Draft -- waiting for blog article review before publishing
**Companion to:** /blog/the-bottleneck-moved.html

---

Three weeks into using Claude Code full-time on personal projects, I stopped writing code.

Not entirely. But the balance shifted. I was generating working implementations faster than I could decide what to build next. The bottleneck had moved from writing code to planning, prioritizing, and coordinating work.

Wes McKinney, creator of pandas, described a similar shift. He's building projects in Go now because AI agents made language fluency less important than fast feedback loops. When agents handle the implementation, what matters is how you organize the work.

I started running four to six Claude Code agents in parallel and hit the same problems any software team hits: duplicate work, version conflicts, agents stepping on each other. Familiar problems, compressed from days into minutes.

So I reached for familiar solutions. Feature branches. Work queues. Claim systems. CI pipelines. The coordination patterns we've developed across decades of software teams work for multi-agent workflows too. The workers are different. The coordination problems are the same.

I've been iterating on a Claude project template that codifies these patterns: 19 custom skills, a work queue for concurrent agents, automated ship pipelines, and template synchronization across projects. I wrote a deep walkthrough on my blog.

Blog: https://janewilkin.dev/blog/the-bottleneck-moved.html
Template: https://github.com/janewilkin/claude-project-template

I think sharing Claude configurations is becoming the new sharing dotfiles. If you're working with Claude Code, I'd be curious to hear what patterns you've found.
