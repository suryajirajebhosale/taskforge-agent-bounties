"""End-to-end: Oracle's grading and dispute-resolution flow, driving the Reputation &
Leaderboard Module in real time over HTTP — the write path the Reputation PRD calls
out explicitly ("record_outcome... called by the Oracle Verification Service after
every final Verdict").
"""

from .conftest import AGENT_INTERNAL_HEADERS, ESCROW_HEADERS, ORACLE_INTERNAL_HEADERS


def _register_agent(agent_client, *, email, categories):
    dev_resp = agent_client.post("/developers", json={"email": email})
    developer_id = dev_resp.json()["id"]
    agent_resp = agent_client.post(
        f"/developers/{developer_id}/agents",
        json={"name": f"agent-for-{email}", "categories": categories, "integration_mode": "poll"},
    )
    body = agent_resp.json()
    return developer_id, body["agent"]["id"], body["api_key"]


def _fund_match_submit(escrow_client, agent_client, *, job_id, category, agent_id, api_key, amount_cents, payload):
    escrow_client.post(
        "/internal/escrow/fund",
        json={"job_id": job_id, "requester_id": "req-rep", "amount_cents": amount_cents},
        headers=ESCROW_HEADERS,
    )
    agent_client.post(
        "/internal/jobs/fund",
        json={"job_id": job_id, "agent_id": agent_id, "category": category, "objective_schema": {}},
        headers=AGENT_INTERNAL_HEADERS,
    )
    return agent_client.post(
        "/submissions", json={"job_id": job_id, "payload": payload}, headers={"Authorization": f"Bearer {api_key}"}
    ).json()


def test_a_passing_verdict_raises_the_agents_rating_and_leaderboard_earnings(
    escrow_client, agent_client, oracle_client, reputation_client
):
    oracle_test_client, _judge, _dispute_judge = oracle_client
    job_id = "e2e-rep-happy"
    category = "other"
    developer_id, agent_id, api_key = _register_agent(agent_client, email="dev-rep@example.com", categories=[category])

    assert reputation_client.get(f"/agents/{agent_id}/rating").json()["rating"] == 0.0

    submission = _fund_match_submit(
        escrow_client, agent_client, job_id=job_id, category=category, agent_id=agent_id, api_key=api_key, amount_cents=1_000, payload={}
    )

    verify_resp = oracle_test_client.post(
        "/internal/verify",
        json={
            "submission_id": submission["id"],
            "job_id": job_id,
            "agent_id": agent_id,
            "agent_developer_id": developer_id,
            "category": category,
            "requirement": {"objective_criteria": [], "subjective_criteria": [{"description": "quality", "weight": 1.0}]},
            "payload": {},
            "job_amount_cents": 1_000,
        },
        headers=ORACLE_INTERNAL_HEADERS,
    )
    assert verify_resp.json()["final_result"] == "pass"

    rating_resp = reputation_client.get(f"/agents/{agent_id}/rating")
    assert rating_resp.json()["rating"] == 5.0
    assert rating_resp.json()["verified_count"] == 1

    leaderboard = reputation_client.get("/leaderboard?period=all_time").json()
    assert leaderboard[0]["agent_id"] == agent_id
    assert leaderboard[0]["verified_earnings_cents"] == 1_000


def test_a_dispute_overturn_corrects_the_rating_through_oracle(escrow_client, agent_client, oracle_client, reputation_client):
    oracle_test_client, judge, dispute_judge = oracle_client
    job_id = "e2e-rep-dispute"
    category = "other"
    developer_id, agent_id, api_key = _register_agent(agent_client, email="dev-rep-2@example.com", categories=[category])

    from services.oracle_service.judge_agent import JudgeVerdict

    judge.verdict = JudgeVerdict(passed=False, confidence=0.9, rationale="initially judged as failing")

    submission = _fund_match_submit(
        escrow_client, agent_client, job_id=job_id, category=category, agent_id=agent_id, api_key=api_key, amount_cents=2_000, payload={}
    )
    requirement = {"objective_criteria": [], "subjective_criteria": [{"description": "quality", "weight": 1.0}]}

    verify_resp = oracle_test_client.post(
        "/internal/verify",
        json={
            "submission_id": submission["id"],
            "job_id": job_id,
            "agent_id": agent_id,
            "agent_developer_id": developer_id,
            "category": category,
            "requirement": requirement,
            "payload": {},
            "job_amount_cents": 2_000,
        },
        headers=ORACLE_INTERNAL_HEADERS,
    )
    verdict_id = verify_resp.json()["id"]
    assert verify_resp.json()["final_result"] == "fail"

    # The initial fail is reflected in the agent's rating and does NOT show on the leaderboard.
    assert reputation_client.get(f"/agents/{agent_id}/rating").json()["rating"] == 0.0
    assert reputation_client.get("/leaderboard?period=all_time").json() == []

    # Agent developer disputes; the independent regrade disagrees, overturning the verdict.
    dispute_judge.verdict = JudgeVerdict(passed=True, confidence=0.95, rationale="independent review: actually passes")
    dispute_resp = oracle_test_client.post(
        "/internal/disputes",
        json={"verdict_id": verdict_id, "raised_by": developer_id, "payload": {}, "requirement": requirement},
        headers=ORACLE_INTERNAL_HEADERS,
    )
    dispute_id = dispute_resp.json()["id"]

    resolve_resp = oracle_test_client.post(
        f"/internal/disputes/{dispute_id}/resolve", json={"resolved_by": "ops-1"}, headers=ORACLE_INTERNAL_HEADERS
    )
    assert resolve_resp.json()["resolution"] == "overturned"

    # The rating now reflects the corrected (passing) outcome, not the original fail —
    # and it still counts as exactly one verified outcome, not two.
    rating_resp = reputation_client.get(f"/agents/{agent_id}/rating")
    assert rating_resp.json()["rating"] == 5.0
    assert rating_resp.json()["verified_count"] == 1

    leaderboard = reputation_client.get("/leaderboard?period=all_time").json()
    assert leaderboard[0]["agent_id"] == agent_id
    assert leaderboard[0]["verified_earnings_cents"] == 2_000

    # And escrow was released only once the dispute overturned it in the agent's favor.
    release_check = escrow_client.post(
        f"/internal/escrow/{job_id}/release", json={"agent_developer_id": developer_id}, headers=ESCROW_HEADERS
    )
    assert release_check.json()["agent_developer_id"] == developer_id
