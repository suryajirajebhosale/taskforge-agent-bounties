import httpx

from services.agent_platform.reputation import HttpReputationReader, NullReputationReader


def test_null_reputation_reader_rates_everyone_zero():
    reader = NullReputationReader()
    assert reader.get_rating("any-agent") == 0.0


def test_http_reputation_reader_parses_the_rating_from_the_response():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/agents/agent-1/rating"
        return httpx.Response(200, json={"agent_id": "agent-1", "rating": 4.2, "verified_count": 10})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://reputation.test")
    reader = HttpReputationReader(base_url="http://reputation.test", client=client)

    assert reader.get_rating("agent-1") == 4.2
