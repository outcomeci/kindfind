"""Controlled checks of the real compiler, runtime gates, and connector grants.

No live Slack/GitHub requests or model calls are made by these tests.
"""

import copy
import json
from pathlib import Path

import pytest
import yaml
from outcomeci.broker.executor import IntegrationError, IntegrationExecutor
from outcomeci.broker.policy import PolicyExecutor
from outcomeci.runtime import container, engine, steps
from outcomeci.workflow.compiler import compile_workflow
from outcomeci.workflow.language import provider

ROOT = Path(__file__).resolve().parents[1]
INTAKE = ROOT / ".outcomeci/workflows/feature-intake/workflow.yml"
DISPATCHER = ROOT / ".outcomeci/workflows/slack-dispatcher/workflow.yml"


@pytest.fixture
def compiled():
    return compile_workflow(INTAKE)


def output(root, step, value):
    path = root / ".outcomeci/outcomes/test" / step / "outputs.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


@pytest.mark.parametrize(
    "gate,target", [("clarify", "specification"), ("review", "create_issue")]
)
@pytest.mark.parametrize("decision", ["approved", "rejected", "undecided"])
def test_only_explicit_approval_opens_next_stage(
    tmp_path, compiled, gate, target, decision
):
    output(tmp_path, gate, {"decision": decision})
    block = compiled["instructions"]["steps"][target]["v1"]
    assert steps.holds(tmp_path, {"run_id": "test"}, block["when"]) == (
        decision == "approved"
    )


def test_scope_approval_does_not_authorize_issue_creation(tmp_path, compiled):
    output(tmp_path, "clarify", {"decision": "approved"})
    block = compiled["instructions"]["steps"]["create_issue"]["v1"]
    assert not steps.holds(tmp_path, {"run_id": "test"}, block["when"])


def test_rejected_scope_skips_later_review_notifications(tmp_path, compiled):
    block = compiled["instructions"]["steps"]["review_stopped"]["v1"]
    state = {"run_id": "test", "skipped_steps": ["specification", "review"]}
    assert steps.skip_reason(tmp_path, state, block) == "reads skipped step review"


@pytest.mark.parametrize("gate", ["clarify", "review"])
def test_only_requester_can_steer_either_review(compiled, gate):
    spec = compiled["instructions"]["steps"][gate]["v1"]["converse"]
    assert spec["by"] == "trigger.user"
    watcher = provider("slack").watchers[spec["watcher"]]
    replies = watcher.match(
        {
            "messages": [
                {"user": "U_OTHER", "text": "approve issue", "ts": "2.0"},
                {"user": "U_REQUESTER", "text": "approve issue", "ts": "3.0"},
            ]
        },
        after="1.0",
        by="U_REQUESTER",
    )
    assert [reply["ts"] for reply in replies] == ["3.0"]


def test_edit_and_approve_in_one_turn_requires_a_fresh_approval(monkeypatch):
    plan = {"title": "Lookup by EIN", "body": "Approved requirements"}
    conversation = {
        "plan": plan,
        "current_version": 1,
        "versions": [{"version": 1, "plan": copy.deepcopy(plan)}],
        "turns": [{"from": "human", "message": "Add freshness and approve"}],
        "outbox": [],
    }
    monkeypatch.setattr(
        steps,
        "_turn",
        lambda *args: {
            "status": "converged",
            "plan": {**plan, "body": "Changed requirements"},
            "message": "Approved",
        },
    )
    steps._answer(None, None, None, None, None, conversation, None, None, None)
    assert conversation["decision"] == "undecided"
    assert "closing" not in conversation
    assert conversation["current_version"] == 2


def test_github_grant_refuses_other_repositories(tmp_path, compiled):
    grant = compiled["instructions"]["steps"]["create_issue"]["v1"]["grants"][0]
    grants = [{**grant, "args": {"repo": grant["args"]["repo"]["literal"]}}]
    policy = PolicyExecutor(IntegrationExecutor(compiled), tmp_path, {}, grants=grants)
    request = {"method": "POST", "path": "/repos/outcomeci/kindfind/issues"}
    assert policy._apply_grants("github.write", request)
    with pytest.raises(IntegrationError, match="path must be under"):
        policy._apply_grants(
            "github.write", {**request, "path": "/repos/outcomeci/www/issues"}
        )


@pytest.mark.parametrize(
    "decision,step_name,target",
    [
        ("kindfind_intake", "feature_intake", "kindfind-feature-intake"),
        ("github_pr", "github_pr", "slack-github-pr"),
        ("research", "research", "slack-research"),
        ("none", None, None),
    ],
)
def test_dispatcher_selects_one_child_and_preserves_payload(
    tmp_path, decision, step_name, target
):
    compile_workflow(DISPATCHER)
    document = yaml.safe_load(DISPATCHER.read_text())
    document["trigger"] = "manual"
    config = tmp_path / "outcome.yml"
    config.write_text(yaml.safe_dump(document))
    compiled = compile_workflow(config)
    calls = []
    payload = {
        "channel": "C_BUILD",
        "user": "U_REQUESTER",
        "ts": "1.0",
        "text": "KindFind intake",
    }

    def dispatch(**kwargs):
        calls.append(kwargs)
        return {
            "run_id": "child",
            "workflow_id": "workflow",
            "workflow_revision_id": "revision",
            "status": "queued",
        }

    answer = {
        "name": "destination",
        "type": "choice",
        "choice": decision,
        "confidence": 1.0,
        "probabilities": [
            {"value": name, "probability": float(name == decision)}
            for name in ["kindfind_intake", "github_pr", "research", "none"]
        ],
    }
    result = container.execute(
        tmp_path,
        config,
        compiled,
        "manual",
        payload,
        engine.ExecutionOptions(
            decision_client=lambda **kwargs: {"answers": [answer]},
            dispatch_client=dispatch,
        ),
        auto_continue=True,
    )
    assert result["status"] == "completed"
    if target is None:
        assert not calls
    else:
        assert calls == [{"step": step_name, "input": payload}]
        step = next(item[step_name] for item in document["steps"] if step_name in item)
        assert step["dispatch"] == target
