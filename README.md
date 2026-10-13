# KindFind

KindFind is a planned MCP/API service that makes 501(c)(3) organization
information accessible to agents. This public repository follows its development
as a series, beginning with human-reviewed feature intake.

## Feature intake from Slack

The OutcomeCI `slack-dispatcher` routes KindFind feature requests to
`kindfind-feature-intake`. Mention the existing OutcomeCI Slack app in `#build`
or send it a DM, for example:

> KindFind feature intake: let an agent look up an organization by EIN and see
> source provenance and when the record was last updated.

The workflow reads this repository and existing issues, discusses scope with
the requester, drafts a Spec Kit-style feature issue, and asks for a second
approval of the exact issue title and body. Reply in the originating thread.
Changes require another approval; rejection or timeout creates no issue.
After final approval, the workflow creates one issue here and replies with its
link. It does not implement code or open a pull request.

The issue captures the specification and clarification stage of
[Spec Kit](https://github.com/github/spec-kit), including prioritized scenarios,
testable requirements, measurable outcomes, assumptions, and an implementation
handoff. Technical planning, tasks, and implementation follow separately.

Workflow source: [`.outcomeci/workflows/feature-intake/workflow.yml`](.outcomeci/workflows/feature-intake/workflow.yml).
Dispatcher source: [`.outcomeci/workflows/slack-dispatcher/workflow.yml`](.outcomeci/workflows/slack-dispatcher/workflow.yml).

Each workflow has its own folder under `.outcomeci/workflows/`. The intake's
Markdown instructions sit beside its YAML definition, referenced by filename
(for example, `reason: scope.md`). Decision-field instructions in the dispatcher
remain inline because the workflow language expects text for those fields.

Pull requests validate these committed bundles with
[`outcomeci/workflow-sync-action`](https://github.com/outcomeci/workflow-sync-action).
The publishing job is installed but gated by `OUTCOMECI_SYNC_ENABLED=true`.
Before enabling it, configure `OUTCOMECI_WORKSPACE_ID` and the `OUTCOMECI_TOKEN`
Actions secret, complete the Vault grants below, and reconcile ownership of
the existing cloud workflows. The pre-existing inline intake and shared
dispatcher are not silently overwritten: the action requires exact-match
adoption before managing an existing workflow, and the new Markdown bundle
differs from the original inline revision. See the action's adoption guidance.
After setup, merges publish changed revisions automatically, with dispatch
children published before their parent. Removed folders retain cloud workflows.

## Operator setup

Publish the child before updating the dispatcher. Grant the child the existing
`slack/bot-token` and `github/pat` Vault entries, preserving their other workflow
grants. No credential values belong in this repository. The Slack app must be
in `#build`; existing mention/DM events and thread reply delivery are reused.
Only the requesting Slack user can steer or approve a request.

The GitHub capability is pinned to this repository. A per-call policy restricts
writes to creating the approved issue. Serial retries search for a hidden hashed
intake marker before creating an issue; concurrent runs are not atomically
deduplicated by GitHub. Each conversation allows 24 turns and expires after two
days. Unapproved drafts remain in Slack and workflow run records.

## Testing

Compile both definitions against OutcomeCI's workflow validator before publishing.
Use the controlled tests in `tests/` for approval gates and dispatch routing.
Live acceptance requires a real Slack mention/DM, both requester approvals, and
verification of the resulting issue and Slack reply. A syntax check or controlled
test is not a live end-to-end result.

With a current OutcomeCI CLI and pytest installed, run:

```sh
python -m pytest tests -q
```

These tests exercise the real compiler, runtime conditions, Slack reply filter,
and GitHub repository grant with controlled inputs. They do not assess live
model routing accuracy or replace the Slack-to-issue acceptance test.
