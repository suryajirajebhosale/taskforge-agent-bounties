from typing import Protocol


class EscrowClient(Protocol):
    def release_to_agent(self, *, job_id: str, agent_developer_id: str) -> dict: ...
    def refund_to_requester(self, *, job_id: str) -> dict: ...


class AgentPlatformClient(Protocol):
    def record_verdict(self, *, job_id: str, submission_id: str, passed: bool) -> dict: ...


class ReputationClient(Protocol):
    def record_outcome(
        self, *, verdict_id: str, agent_id: str, agent_developer_id: str, passed: bool, job_amount_cents: int
    ) -> dict: ...

    def correct_outcome(
        self, *, verdict_id: str, agent_id: str, agent_developer_id: str, passed: bool, job_amount_cents: int
    ) -> dict: ...


class HttpEscrowClient:
    def __init__(self, base_url: str, internal_api_key: str, client=None):
        import httpx

        self._client = client or httpx.Client(base_url=base_url, timeout=10.0)
        self._headers = {"X-Internal-Api-Key": internal_api_key}

    def release_to_agent(self, *, job_id: str, agent_developer_id: str) -> dict:
        response = self._client.post(
            f"/internal/escrow/{job_id}/release",
            json={"agent_developer_id": agent_developer_id},
            headers=self._headers,
        )
        response.raise_for_status()
        return response.json()

    def refund_to_requester(self, *, job_id: str) -> dict:
        response = self._client.post(
            f"/internal/escrow/{job_id}/refund",
            headers=self._headers,
        )
        response.raise_for_status()
        return response.json()


class HttpAgentPlatformClient:
    def __init__(self, base_url: str, internal_api_key: str, client=None):
        import httpx

        self._client = client or httpx.Client(base_url=base_url, timeout=10.0)
        self._headers = {"X-Internal-Api-Key": internal_api_key}

    def record_verdict(self, *, job_id: str, submission_id: str, passed: bool) -> dict:
        response = self._client.post(
            f"/internal/jobs/{job_id}/verdict",
            json={"submission_id": submission_id, "passed": passed},
            headers=self._headers,
        )
        response.raise_for_status()
        return response.json()


class HttpReputationClient:
    def __init__(self, base_url: str, internal_api_key: str, client=None):
        import httpx

        self._client = client or httpx.Client(base_url=base_url, timeout=10.0)
        self._headers = {"X-Internal-Api-Key": internal_api_key}

    def record_outcome(
        self, *, verdict_id: str, agent_id: str, agent_developer_id: str, passed: bool, job_amount_cents: int
    ) -> dict:
        response = self._client.post(
            "/internal/outcomes",
            json={
                "verdict_id": verdict_id,
                "agent_id": agent_id,
                "agent_developer_id": agent_developer_id,
                "passed": passed,
                "job_amount_cents": job_amount_cents,
            },
            headers=self._headers,
        )
        response.raise_for_status()
        return response.json()

    def correct_outcome(
        self, *, verdict_id: str, agent_id: str, agent_developer_id: str, passed: bool, job_amount_cents: int
    ) -> dict:
        response = self._client.post(
            f"/internal/outcomes/{verdict_id}/correct",
            json={
                "agent_id": agent_id,
                "agent_developer_id": agent_developer_id,
                "passed": passed,
                "job_amount_cents": job_amount_cents,
            },
            headers=self._headers,
        )
        response.raise_for_status()
        return response.json()
