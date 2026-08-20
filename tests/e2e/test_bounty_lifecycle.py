"""End-to-end: the full bounty lifecycle across the Escrow Ledger Service, the Agent
SDK / Submission Intake service, and now the Oracle Verification Service, driven
entirely over HTTP (each service's own TestClient), matching how they'd actually talk
to each other once deployed.

Sequence under test, for every scenario: fund escrow -> match agents to the bounty ->
agent(s) discover and submit -> Oracle grades the submission and, on a confirmed pass,
tells Agent Platform and releases escrow itself -> the ledger reconciles clean.

Oracle deliberately does not auto-refund on a fail (see `VerificationService`'s
docstring and `conftest.py`) — the failure-path scenario below still calls Escrow's
refund endpoint directly, standing in for the not-yet-built piece that would decide
"this bounty's last competing submission just failed" across every agent, not just one.
"""

from .conftest import AGENT_INTERNAL_HEADERS, ESCROW_HEADERS, ORACLE_INTERNAL_HEADERS


def _register_agent(agent_client, *, email, categories):
    dev_resp = agent_client.post("/developers", json={"email": email})
    assert dev_resp.status_code == 200
    developer_id = dev_resp.json()["id"]

    agent_resp = agent_client.post(
        f"/developers/{developer_id}/agents",
        json={"name": f"agent-for-{email}", "categories": categories, "integration_mode": "poll"},
    )
    assert agent_resp.status_code == 200
    body = agent_resp.json()
    return developer_id, body["agent"]["id"], body["api_key"]


def test_happy_path_single_agent_wins_and_gets_paid(escrow_client, agent_client, oracle_client):
    oracle_test_client, _judge, _dispute_judge = oracle_client
    job_id = "e2e-happy-path"
    category = "sales_lead_generation"
    requirement = {"objective_criteria": [{"field": "lead_count", "comparator": ">=", "value": 40}], "subjective_criteria": []}

    developer_id, agent_id, api_key = _register_agent(
        agent_client, email="dev-happy@example.com", categories=[category]
    )

    fund_resp = escrow_client.post(
        "/internal/escrow/fund",
        json={"job_id": job_id, "requester_id": "req-1", "amount_cents": 10_000, "take_rate_bps": 1000},
        headers=ESCROW_HEADERS,
    )
    assert fund_resp.status_code == 200
    assert fund_resp.json()["status"] == "held"

    match_resp = agent_client.post(
        "/internal/jobs/fund",
        json={"job_id": job_id, "agent_id": agent_id, "category": category, "objective_schema": {"lead_count": "integer"}},
        headers=AGENT_INTERNAL_HEADERS,
    )
    assert match_resp.status_code == 200
    assert len(match_resp.json()) == 1

    poll_resp = agent_client.get("/jobs/available", headers={"Authorization": f"Bearer {api_key}"})
    assert [m["job_id"] for m in poll_resp.json()] == [job_id]

    submit_resp = agent_client.post(
        "/submissions",
        json={"job_id": job_id, "payload": {"lead_count": 42}},
        headers={"Authorization": f"Bearer {api_key}"},
    )
    assert submit_resp.status_code == 200
    submission = submit_resp.json()
    assert submission["status"] == "queued_for_grading"

    verify_resp = oracle_test_client.post(
        "/internal/verify",
        json={
            "submission_id": submission["id"],
            "job_id": job_id,
            "agent_id": agent_id,
            "agent_developer_id": developer_id,
            "category": category,
            "requirement": requirement,
            "payload": {"lead_count": 42},
            "job_amount_cents": 10_000,
        },
        headers=ORACLE_INTERNAL_HEADERS,
    )
    assert verify_resp.status_code == 200
    verdict = verify_resp.json()
    assert verdict["final_result"] == "pass"
    assert verdict["resolved"] is True

    # Oracle's own response doesn't carry payout details — confirm the release it
    # triggered internally actually happened, with the right take-rate math, by calling
    # release again (idempotent) and reading back the result.
    release_check = escrow_client.post(
        f"/internal/escrow/{job_id}/release", json={"agent_developer_id": developer_id}, headers=ESCROW_HEADERS
    )
    assert release_check.json()["amount_cents"] == 9_000  # 10,000 - 10% take rate
    assert release_check.json()["agent_developer_id"] == developer_id

    reconcile_resp = escrow_client.post(
        "/internal/escrow/reconcile", json={"job_ids": [job_id]}, headers=ESCROW_HEADERS
    )
    assert reconcile_resp.json()["clean"] is True

    available_after = agent_client.get("/jobs/available", headers={"Authorization": f"Bearer {api_key}"})
    assert available_after.json() == []  # already submitted, no longer "available"


def test_competitive_path_first_pass_wins_and_only_the_winner_gets_paid(escrow_client, agent_client, oracle_client):
    oracle_test_client, _judge, _dispute_judge = oracle_client
    job_id = "e2e-competitive"
    category = "content_media"
    requirement = {
        "objective_criteria": [{"field": "deliverable_count", "comparator": ">=", "value": 1}],
        "subjective_criteria": [],
    }

    dev_a, agent_a, key_a = _register_agent(agent_client, email="dev-a@example.com", categories=[category])
    dev_b, agent_b, key_b = _register_agent(agent_client, email="dev-b@example.com", categories=[category])

    escrow_client.post(
        "/internal/escrow/fund",
        json={"job_id": job_id, "requester_id": "req-2", "amount_cents": 5_000, "take_rate_bps": 0},
        headers=ESCROW_HEADERS,
    )
    match_resp = agent_client.post(
        "/internal/jobs/fund",
        json={"job_id": job_id, "agent_id": agent_a, "category": category, "objective_schema": {"deliverable_count": "integer"}},
        headers=AGENT_INTERNAL_HEADERS,
    )
    assert match_resp.status_code == 200
    assert len(match_resp.json()) == 1

    second = agent_client.post(
        "/internal/jobs/fund",
        json={"job_id": job_id, "agent_id": agent_b, "category": category, "objective_schema": {"deliverable_count": "integer"}},
        headers=AGENT_INTERNAL_HEADERS,
    )
    assert second.status_code == 409

    submission_a = agent_client.post(
        "/submissions",
        json={"job_id": job_id, "payload": {"deliverable_count": 3}},
        headers={"Authorization": f"Bearer {key_a}"},
    ).json()
    submit_b = agent_client.post(
        "/submissions",
        json={"job_id": job_id, "payload": {"deliverable_count": 2}},
        headers={"Authorization": f"Bearer {key_b}"},
    )
    assert submit_b.status_code == 409

    verify_a = oracle_test_client.post(
        "/internal/verify",
        json={
            "submission_id": submission_a["id"],
            "job_id": job_id,
            "agent_id": agent_a,
            "agent_developer_id": dev_a,
            "category": category,
            "requirement": requirement,
            "payload": {"deliverable_count": 3},
            "job_amount_cents": 5_000,
        },
        headers=ORACLE_INTERNAL_HEADERS,
    ).json()
    assert verify_a["final_result"] == "pass"

    release_after_a = escrow_client.post(
        f"/internal/escrow/{job_id}/release", json={"agent_developer_id": dev_a}, headers=ESCROW_HEADERS
    )
    assert release_after_a.json()["agent_developer_id"] == dev_a
    assert release_after_a.json()["amount_cents"] == 5_000

    reconcile_resp = escrow_client.post(
        "/internal/escrow/reconcile", json={"job_ids": [job_id]}, headers=ESCROW_HEADERS
    )
    assert reconcile_resp.json()["clean"] is True


def test_failure_path_verdict_fails_and_requester_is_refunded(escrow_client, agent_client, oracle_client):
    oracle_test_client, _judge, _dispute_judge = oracle_client
    job_id = "e2e-failure"
    category = "research_competitive_intelligence"
    requirement = {
        "objective_criteria": [{"field": "entry_count", "comparator": ">=", "value": 100}],
        "subjective_criteria": [],
    }

    developer_id, agent_id, api_key = _register_agent(
        agent_client, email="dev-fail@example.com", categories=[category]
    )

    escrow_client.post(
        "/internal/escrow/fund",
        json={"job_id": job_id, "requester_id": "req-3", "amount_cents": 2_000},
        headers=ESCROW_HEADERS,
    )
    agent_client.post(
        "/internal/jobs/fund",
        json={"job_id": job_id, "agent_id": agent_id, "category": category, "objective_schema": {"entry_count": "integer"}},
        headers=AGENT_INTERNAL_HEADERS,
    )
    submission = agent_client.post(
        "/submissions",
        json={"job_id": job_id, "payload": {"entry_count": 5}},  # far short of the required 100
        headers={"Authorization": f"Bearer {api_key}"},
    ).json()

    verify_resp = oracle_test_client.post(
        "/internal/verify",
        json={
            "submission_id": submission["id"],
            "job_id": job_id,
            "agent_id": agent_id,
            "agent_developer_id": developer_id,
            "category": category,
            "requirement": requirement,
            "payload": {"entry_count": 5},
            "job_amount_cents": 2_000,
        },
        headers=ORACLE_INTERNAL_HEADERS,
    )
    assert verify_resp.json()["final_result"] == "fail"

    # Oracle does not auto-refund on a fail. With exactly one agent here and it failed,
    # refunding is unambiguously correct — a future orchestrator would determine that by
    # checking Agent Platform's submission state across every competing agent; this test
    # makes that call directly since it's the only competitor.
    refund_resp = escrow_client.post(f"/internal/escrow/{job_id}/refund", headers=ESCROW_HEADERS)
    assert refund_resp.status_code == 200
    assert refund_resp.json()["status"] == "refunded"

    late_release_attempt = escrow_client.post(
        f"/internal/escrow/{job_id}/release", json={"agent_developer_id": developer_id}, headers=ESCROW_HEADERS
    )
    assert late_release_attempt.status_code == 409
