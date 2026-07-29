import time
from typing import Protocol


class WebhookTransport(Protocol):
    def post(self, url: str, json_body: dict) -> int:
        """Delivers one POST. Returns the HTTP status code. Raises on connection-level
        failure (timeout, DNS, refused connection, etc.) — that's treated as a failed
        attempt, same as a non-2xx response."""
        ...


class HttpxWebhookTransport:
    def __init__(self, client=None):
        import httpx

        self._client = client or httpx.Client(timeout=5.0)

    def post(self, url: str, json_body: dict) -> int:
        response = self._client.post(url, json=json_body)
        return response.status_code


class WebhookNotifier:
    """Delivers bounty-match notifications to webhook-mode agents, retrying transient
    failures with backoff. A non-2xx status and a transport-level exception both count
    as a failed attempt and trigger the next retry."""

    def __init__(
        self,
        transport: WebhookTransport,
        backoff_seconds: list[float] | None = None,
        sleep_fn=time.sleep,
    ):
        self._transport = transport
        self._backoff_seconds = backoff_seconds if backoff_seconds is not None else [0, 1, 5]
        self._sleep_fn = sleep_fn

    def deliver(self, *, url: str, payload: dict) -> tuple[bool, int, str | None]:
        """Returns (delivered, attempts_made, last_error)."""
        last_error: str | None = None
        attempts = 0
        for delay in self._backoff_seconds:
            if delay:
                self._sleep_fn(delay)
            attempts += 1
            try:
                status = self._transport.post(url, payload)
            except Exception as exc:  # noqa: BLE001 - any transport failure is retryable
                last_error = str(exc)
                continue
            if 200 <= status < 300:
                return True, attempts, None
            last_error = f"webhook returned status {status}"
        return False, attempts, last_error
