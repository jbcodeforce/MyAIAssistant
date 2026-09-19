"""JSON-to-form adapter for AgentOS runs endpoint.

AgentOS only accepts ``application/x-www-form-urlencoded`` on
``POST /agents/{name}/runs``.  The Vue frontend sends ``application/json``.
This thin router intercepts JSON requests, re-encodes them as form data,
and forwards them to the AgentOS handler via an httpx sub-request so the
real handler can stream SSE back to the caller.

Form-encoded requests are NOT intercepted — they pass straight through to
the AgentOS-mounted route, exactly as before.
"""

import logging
import os

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import Response, StreamingResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["agents-json-adapter"])

_PORT = int(os.environ.get("AGENT_SERVICE_PORT", "8100").strip())
_AGENTOSS_BASE = f"http://127.0.0.1:{_PORT}"

# Headers that must not be forwarded upstream (httpx sets them itself).
_HOP_BY_HOP = frozenset(
    [
        "host",
        "content-length",
        "transfer-encoding",
        "connection",
        "keep-alive",
        "te",
        "trailers",
        "upgrade",
    ]
)


def _forward_headers(request: Request, override: dict | None = None) -> dict:
    """Build a filtered header dict suitable for forwarding upstream."""
    headers = {k: v for k, v in request.headers.items() if k.lower() not in _HOP_BY_HOP}
    if override:
        headers.update(override)
    return headers


async def _stream_from_upstream(client: httpx.AsyncClient, method: str, url: str, **kwargs):
    """Async generator that keeps the httpx client alive while yielding response chunks.

    Yields the response object as the *first* item so callers can read
    status code / headers before consuming the body.
    """
    async with client.stream(method, url, **kwargs) as upstream:
        yield upstream
        async for chunk in upstream.aiter_bytes():
            yield chunk


@router.post("/agents/{agent_name}/runs")
async def json_to_form_adapter(agent_name: str, request: Request):
    """Intercept JSON POSTs and re-dispatch as form-encoded to AgentOS."""
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        # Parse JSON and re-encode as form data.
        try:
            payload = await request.json()
        except Exception:
            payload = {}
        form_data = {k: str(v) for k, v in payload.items()}
        forward_hdrs = _forward_headers(
            request, {"content-type": "application/x-www-form-urlencoded"}
        )
    else:
        # Not JSON — forward raw body unchanged (passthrough for form-encoded).
        body = await request.body()
        forward_hdrs = _forward_headers(request)
        form_data = None

    target_url = f"{_AGENTOSS_BASE}/agents/{agent_name}/runs"
    query_params = dict(request.query_params)

    logger.debug(
        "JSON→form adapter forwarding to %s (json=%s)", target_url, form_data is not None
    )

    if form_data is not None:
        # Streaming forward — keep client alive inside the generator.
        async def _iter_streaming():
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "POST",
                    target_url,
                    data=form_data,
                    headers=forward_hdrs,
                    params=query_params,
                ) as upstream:
                    async for chunk in upstream.aiter_bytes():
                        yield chunk

        # We need the response metadata (status, headers) before we can
        # construct the StreamingResponse.  Open the connection eagerly,
        # read *nothing* from the body yet, then hand the generator back.
        client = httpx.AsyncClient(timeout=None)
        upstream = await client.send(
            client.build_request(
                "POST",
                target_url,
                data=form_data,
                headers=forward_hdrs,
                params=query_params,
            ),
            stream=True,
        )

        status = upstream.status_code
        resp_headers = {
            k: v for k, v in upstream.headers.items() if k.lower() not in _HOP_BY_HOP
        }
        media_type = upstream.headers.get("content-type", "application/octet-stream")

        async def _body_gen(resp=upstream, http_client=client):
            try:
                async for chunk in resp.aiter_bytes():
                    yield chunk
            finally:
                await resp.aclose()
                await http_client.aclose()

        return StreamingResponse(
            content=_body_gen(),
            status_code=status,
            headers=resp_headers,
            media_type=media_type,
        )

    else:
        # Passthrough: forward raw body, buffer response (no streaming needed
        # for form-encoded requests that arrive here — they go straight to
        # AgentOS normally, but we handle the edge case defensively).
        async with httpx.AsyncClient(timeout=None) as client:
            upstream = await client.post(
                target_url,
                content=body,
                headers=forward_hdrs,
                params=query_params,
            )
        resp_headers = {
            k: v for k, v in upstream.headers.items() if k.lower() not in _HOP_BY_HOP
        }
        return Response(
            content=upstream.content,
            status_code=upstream.status_code,
            headers=resp_headers,
            media_type=upstream.headers.get("content-type"),
        )
