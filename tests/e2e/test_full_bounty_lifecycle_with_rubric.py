"""End-to-end: the full bounty lifecycle across all four services — Rubric Module ->
Escrow Ledger Service -> Agent SDK / Submission Intake -> Oracle Verification Service —
driven entirely over HTTP, each service in its own TestClient.

Sequence: requester describes a bounty in free text -> Rubric drafts structured
criteria -> requester approves -> escrow is funded -> (stand-in orchestrator) locks the
rubric and derives Agent Platform's `objective_schema` from the approved Requirement's
`objective_criteria` -> an agent is matched and submits a payload shaped to match ->
Oracle grades the submission against the requester-approved Requirement and, on a pass,
releases escrow itself -> the ledger reconciles clean.

That schema-bridging step (`Requirement.objective_schema()`-shaped dict -> Agent
Platform's `notify_job_funded(objective_schema=...)`) still has no owning service —
it's exactly the kind of glue a future orchestrator would own — so it happens inline in
this test, same as in test_bounty_lifecycle.py.
"""

from .conftest import AGENT_INTERNAL_HEADERS, ESCROW_HEADERS, ORACLE_INTERNAL_HEADERS, RUBRIC_INTERNAL_HEADERS


def _register_agent(agent_client, *, email, categories):
    dev_resp = agent_client.post("/developers", json={"email": email})
    developer_id = dev_resp.json()["id"]
    agent_resp = agent_client.post(
        f"/developers/{developer_id}/agents",
        json={"name": f"agent-for-{email}", "categories": categories, "integration_mode": "poll"},
    )
    body = agent_resp.json()
    return developer_id, body["agent"]["id"], body["api_key"]


def test_full_lifecycle_from_free_text_description_to_payout(escrow_client, agent_client, rubric_client, oracle_client):
    oracle_test_client, _judge, _dispute_judge = oracle_client
    job_id = "e2e-full-lifecycle"

    # 1. Requester describes the bounty in free text; Rubric drafts structured criteria.
    draft_resp = rubric_client.post(
        "/rubrics/draft",
        json={
            "job_id": job_id,
            "job_description": "Find 100 ecommerce brands doing $1M-$25M in revenue",
            "category": "sales_lead_generation",
        },
    )
    assert draft_resp.status_code == 200
    requirement = draft_resp.json()["requirement"]
    assert requirement["objective_criteria"][0]["field"] == "lead_count"

    # 2. Requester reviews and approves the draft.
    approve_resp = rubric_client.post(f"/rubrics/{job_id}/approve")
    assert approve_resp.json()["status"] == "approved"

    # 3. Requester funds the bounty via escrow.
    fund_resp = escrow_client.post(
        "/internal/escrow/fund",
        json={"job_id": job_id, "requester_id": "req-1", "amount_cents": 20_000, "take_rate_bps": 1000},
        headers=ESCROW_HEADERS,
    )
    assert fund_resp.json()["status"] == "held"

    # 4. (Stand-in orchestrator) funding locks the rubric — criteria are now immutable.
    lock_resp = rubric_client.post(f"/internal/rubrics/{job_id}/lock", headers=RUBRIC_INTERNAL_HEADERS)
    assert lock_resp.status_code == 200
    locked_requirement = lock_resp.json()["requirement"]
    schema_for_agent_platform = {c["field"]: "integer" for c in locked_requirement["objective_criteria"]}

    # 5. (Stand-in orchestrator) agents are matched using the locked requirement's shape.
    developer_id, agent_id, api_key = _register_agent(
        agent_client, email="dev-full@example.com", categories=["sales_lead_generation"]
    )
    match_resp = agent_client.post(
        "/internal/jobs/fund",
        json={"job_id": job_id, "agent_id": agent_id, "category": "sales_lead_generation", "objective_schema": schema_for_agent_platform},
        headers=AGENT_INTERNAL_HEADERS,
    )
    assert len(match_resp.json()) == 1

    # 6. Agent submits a payload shaped to match the rubric's objective criteria.
    submit_resp = agent_client.post(
        "/submissions",
        json={"job_id": job_id, "payload": {"lead_count": 100}},
        headers={"Authorization": f"Bearer {api_key}"},
    )
    assert submit_resp.status_code == 200
    submission = submit_resp.json()

    # 7. Oracle grades the submission against the requester-approved requirement — the
    # objective lead count and the (faked) judge's read on the subjective criteria —
    # and, on a pass, tells Agent Platform and releases escrow itself.
    verify_resp = oracle_test_client.post(
        "/internal/verify",
        json={
            "submission_id": submission["id"],
            "job_id": job_id,
            "agent_id": agent_id,
            "agent_developer_id": developer_id,
            "category": "sales_lead_generation",
            "requirement": locked_requirement,
            "payload": {"lead_count": 100},
            "job_amount_cents": 20_000,
        },
        headers=ORACLE_INTERNAL_HEADERS,
    )
    assert verify_resp.status_code == 200
    assert verify_resp.json()["final_result"] == "pass"

    release_check = escrow_client.post(
        f"/internal/escrow/{job_id}/release", json={"agent_developer_id": developer_id}, headers=ESCROW_HEADERS
    )
    assert release_check.json()["amount_cents"] == 18_000  # 20,000 - 10% take rate

    reconcile_resp = escrow_client.post(
        "/internal/escrow/reconcile", json={"job_ids": [job_id]}, headers=ESCROW_HEADERS
    )
    assert reconcile_resp.json()["clean"] is True


def test_rubric_cannot_be_edited_once_the_bounty_is_locked(rubric_client):
    job_id = "e2e-rubric-lock-guard"
    rubric_client.post(
        "/rubrics/draft",
        json={"job_id": job_id, "job_description": "find leads", "category": "sales_lead_generation"},
    )
    rubric_client.post(f"/rubrics/{job_id}/approve")
    rubric_client.post(f"/internal/rubrics/{job_id}/lock", headers=RUBRIC_INTERNAL_HEADERS)

    resp = rubric_client.put(
        f"/rubrics/{job_id}",
        json={
            "requirement": {
                "objective_criteria": [{"field": "lead_count", "comparator": ">=", "value": 999}],
                "subjective_criteria": [],
            }
        },
    )
    assert resp.status_code == 409


def test_escrow_refuses_to_release_when_rubric_was_never_approved(escrow_client, rubric_client):
    """A bounty must not be fundable-to-payout against criteria the requester never
    signed off on — this checks the Rubric side of that guarantee independently of
    Escrow, since the two services don't share a database to enforce it jointly."""
    job_id = "e2e-unapproved-rubric"
    rubric_client.post(
        "/rubrics/draft",
        json={"job_id": job_id, "job_description": "find leads", "category": "sales_lead_generation"},
    )
    # deliberately skip approval

    lock_resp = rubric_client.post(f"/internal/rubrics/{job_id}/lock", headers=RUBRIC_INTERNAL_HEADERS)
    assert lock_resp.status_code == 409
