"""Async HTTP client with retry and rate-limit awareness."""

from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx

from ghidractl.errors import GitHubAPIError, NetworkError, RateLimitError

_DEFAULT_TIMEOUT = httpx.Timeout(connect=30.0, read=300.0, write=30.0, pool=30.0)
_STREAM_TIMEOUT = httpx.Timeout(connect=30.0, read=1800.0, write=30.0, pool=30.0)
_MAX_RETRIES = 3
_RETRY_BACKOFF = 1.0


class HttpClient:
    """Async HTTP client wrapper with retry and rate-limit handling."""

    def __init__(
        self,
        github_token: str = "",
        timeout: httpx.Timeout = _DEFAULT_TIMEOUT,
        max_retries: int = _MAX_RETRIES,
    ) -> None:
        self._github_token = github_token
        self._timeout = timeout
        self._max_retries = max_retries
        self._client: httpx.AsyncClient | None = None
        self._stream_client: httpx.AsyncClient | None = None

    def _make_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {
            "User-Agent": "ghidractl/0.1.0",
            "Accept": "application/vnd.github+json",
        }
        if self._github_token:
            headers["Authorization"] = f"Bearer {self._github_token}"
        return headers

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                headers=self._make_headers(),
                follow_redirects=True,
            )
        return self._client

    async def _get_stream_client(self) -> httpx.AsyncClient:
        if self._stream_client is None or self._stream_client.is_closed:
            self._stream_client = httpx.AsyncClient(
                timeout=_STREAM_TIMEOUT,
                headers=self._make_headers(),
                follow_redirects=True,
            )
        return self._stream_client

    async def get(self, url: str, **kwargs: Any) -> httpx.Response:
        """GET with retry and rate-limit handling."""
        return await self._request("GET", url, **kwargs)

    async def get_json(self, url: str, **kwargs: Any) -> Any:
        """GET and parse JSON response."""
        resp = await self.get(url, **kwargs)
        return resp.json()

    async def stream(self, url: str, **kwargs: Any) -> httpx.Response:
        """Start a streaming GET request with extended read timeout (caller must close)."""
        client = await self._get_stream_client()
        req = client.build_request("GET", url, **kwargs)
        return await client.send(req, stream=True)

    async def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        """Execute request with retry logic."""
        client = await self._get_client()
        last_exc: Exception | None = None

        for attempt in range(self._max_retries):
            try:
                resp = await client.request(method, url, **kwargs)

                if resp.status_code == 403:
                    remaining = resp.headers.get("x-ratelimit-remaining")
                    if remaining == "0":
                        reset = resp.headers.get("x-ratelimit-reset")
                        reset_at = int(reset) if reset else None
                        raise RateLimitError(reset_at=reset_at)

                if resp.status_code >= 400:
                    raise GitHubAPIError(resp.status_code, resp.text[:200])

                return resp

            except (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout) as exc:
                last_exc = exc
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(_RETRY_BACKOFF * (attempt + 1))
                continue

            except RateLimitError:
                raise

            except GitHubAPIError:
                raise

        raise NetworkError(f"Request failed after {self._max_retries} retries: {last_exc}")

    async def close(self) -> None:
        """Close the underlying HTTP clients."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
        if self._stream_client and not self._stream_client.is_closed:
            await self._stream_client.aclose()
            self._stream_client = None

    async def __aenter__(self) -> HttpClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
