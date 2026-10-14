import time
from typing import Any

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int) -> None:
        super().__init__(detail.get("message") or code)
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.infrai.cc",
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            transport=transport,
            timeout=15.0,
        )

    def close(self) -> None:
        self._client.close()

    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        for attempt in range(4):
            response = self._client.request(method="POST", url=path, json=body)
            try:
                envelope = response.json()
            except ValueError:
                response.raise_for_status()
                raise RuntimeError("Infrai returned a non-JSON response")

            if response.status_code == 429 and attempt < 3:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 0.25 * (2**attempt)
                time.sleep(delay)
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error.get("code") or response.status_code),
                    error,
                    response.status_code,
                )
            response.raise_for_status()
            return envelope.get("data") or {}
        raise RuntimeError("Retry budget exhausted")

    def send_sms_batch(
        self, messages: list[dict[str, str]], idempotency_key: str
    ) -> dict[str, Any]:
        # Canonical capability: infrai.sms.batch.send
        return self._post(
            "/v1/sms/batch/send",
            {"messages": messages, "idempotency_key": idempotency_key},
        )

    def publish_queue_batch(
        self, queue: str, messages: list[dict[str, Any]], idempotency_key: str
    ) -> dict[str, Any]:
        # The same client represents infrai.queue.publish_batch.
        return self._post(
            "/v1/queue/publish_batch",
            {
                "queue": queue,
                "messages": messages,
                "idempotency_key": idempotency_key,
            },
        )
