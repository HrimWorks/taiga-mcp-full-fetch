from __future__ import annotations

from collections.abc import Callable

import httpx
import pytest

from taiga_client import TaigaClient, _extract_pagination


@pytest.fixture()
def anyio_backend() -> str:
    return "asyncio"


def _client(handler: Callable[[httpx.Request], httpx.Response]) -> TaigaClient:
    client = TaigaClient.__new__(TaigaClient)
    client._client = httpx.AsyncClient(
        base_url="https://taiga.example/api/v1",
        transport=httpx.MockTransport(handler),
    )
    return client


@pytest.mark.anyio("asyncio")
async def test_list_epics_fetches_every_server_page() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        page = request.url.params["page"]
        if page == "1":
            return httpx.Response(
                200,
                json=[{"id": item_id} for item_id in range(1, 101)],
                headers={"x-pagination-next": "2"},
            )
        assert page == "2"
        return httpx.Response(200, json=[{"id": 101}])

    client = _client(handler)
    try:
        epics = await client.list_epics(7)
    finally:
        await client.close()

    assert [epic["id"] for epic in epics] == list(range(1, 102))
    assert [request.url.params["page"] for request in requests] == ["1", "2"]
    assert all(request.url.params["page_size"] == "100" for request in requests)
    assert all(request.url.params["project"] == "7" for request in requests)


@pytest.mark.anyio("asyncio")
async def test_full_last_page_does_not_request_nonexistent_page() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=[{"id": item_id} for item_id in range(1, 101)])

    client = _client(handler)
    try:
        projects = await client.list_projects(params={"member": "12"})
    finally:
        await client.close()

    assert len(projects) == 100
    assert len(requests) == 1
    assert requests[0].url.params["page"] == "1"
    assert requests[0].url.params["member"] == "12"


@pytest.mark.parametrize(
    ("headers", "expected"),
    [
        (
            {
                "x-paginated-by": "100",
                "x-pagination-count": "101",
                "x-pagination-current": "1",
                "x-pagination-next": "2",
                "x-pagination-prev": "",
            },
            {"page_size": 100, "total": 101, "page": 1, "next": 2, "previous": None},
        ),
        ({"x-pagination-next": "null"}, {"next": None}),
    ],
)
def test_extract_pagination_supports_taiga_headers(headers, expected) -> None:
    assert _extract_pagination(headers) == expected
