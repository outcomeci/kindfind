Turn clarify.plan into one Spec Kit-style feature issue for outcomeci/kindfind.
Respect the agreed scope and the repository's constitution/specs when present.
Read related issues and cite actual links when helpful. Do not silently select
an implementation stack or data provider that the requester has not selected.

Return plan.title and plan.body as the exact proposed GitHub issue. Keep the
title at most 100 characters and body at most 2700 characters so the runtime's
versioned review fits Slack. Prefer a small feature over compressing a large
initiative into a vague issue. Include these short sections:

- Problem and scope: intended user/agent, outcome, and explicit non-goals.
- User scenarios: prioritized stories, independently testable behavior, and
  concrete Given/When/Then acceptance examples including a failure case.
- Requirements: numbered FR identifiers; data entities and observable MCP/API
  behavior where relevant, with assumptions separated from confirmed choices.
- Success criteria: numbered SC identifiers and measurable, technology-neutral
  outcomes traceable to the acceptance scenarios.
- Implementation handoff: a short checklist for the later Spec Kit plan, tasks,
  and verification work; include unresolved technical choices as research tasks.
- Assumptions and dependencies: include related issues and data freshness or
  provenance constraints when relevant. Do not leave blocking requirements vague.

This is the specify/clarify artifact for later planning, not a claim that code,
formal spec files, a technical plan, or tasks have already been implemented.
Publish only the approved feature information. Omit Slack transcripts, channel
IDs, personal details, private URLs, and credentials. Do not add labels,
assignees, milestones, or a repository field to the plan.

Post exactly one short message in the original thread, mentioning the requester.
Introduce the final issue review and tell them the versioned title/body follows.
Ask for changes or an explicit 'approve issue' after reading it. Approval of the
previous scope does not count as approval of this draft. Do not create an issue.
