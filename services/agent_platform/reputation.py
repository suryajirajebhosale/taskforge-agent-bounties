from typing import Protocol


class ReputationReader(Protocol):
    """What the Agent SDK needs from the Reputation & Leaderboard Module to rank agents
    during matching. Kept as a narrow interface so this service can be built and tested
    before that module exists, per the Reputation module's PRD (`get_rating(agent_id)`
    is designed with this consumer in mind)."""

    def get_rating(self, agent_id: str) -> float: ...


class NullReputationReader:
    """Neutral stand-in. Every agent rates equally, so matching falls back to
    registration order. This remains the default dependency in `main.py` even though
    the Reputation & Leaderboard Module now exists — wiring matching to call it live,
    synchronously, on every bounty-funding event is a real production/availability
    decision (a slow or down Reputation service would then block matching entirely),
    left for a deliberate follow-up rather than a silent default change here."""

    def get_rating(self, agent_id: str) -> float:
        return 0.0


class HttpReputationReader:
    """Real implementation, calling the Reputation & Leaderboard Module's
    `GET /agents/{agent_id}/rating`. Available to wire in once the availability
    trade-off noted on `NullReputationReader` has been made deliberately."""

    def __init__(self, base_url: str, client=None):
        import httpx

        self._client = client or httpx.Client(base_url=base_url, timeout=5.0)

    def get_rating(self, agent_id: str) -> float:
        response = self._client.get(f"/agents/{agent_id}/rating")
        response.raise_for_status()
        return response.json()["rating"]
