"""Pre-scaffolded pytest fixtures for the FastAPI backend.

Tests hit the live uvicorn process managed by supervisor (not an in-process ASGI app), so
the app under test is the same one the frontend and Playwright see. Do NOT re-create this
file — add app-specific fixtures below the marker at the bottom.
"""

import os

import httpx
import pytest
import pytest_asyncio

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
API_URL = f"{BACKEND_URL}/api"


def api_url(path: str = "") -> str:
    """Absolute URL for an /api route: api_url("/status") -> http://localhost:8001/api/status."""
    return f"{API_URL}{path}"


@pytest.fixture(scope="session")
def backend_url() -> str:
    return BACKEND_URL


@pytest.fixture
def client():
    """Sync httpx client rooted at /api — the default for endpoint tests.

    Example:
        def test_status(client):
            assert client.get("/status").status_code == 200
    """
    with httpx.Client(base_url=API_URL, timeout=30.0) as c:
        yield c


@pytest_asyncio.fixture
async def aclient():
    """Async variant, for tests that also await motor/backend helpers directly."""
    async with httpx.AsyncClient(base_url=API_URL, timeout=30.0) as c:
        yield c


# --- app-specific fixtures below this line ---


def login_client(client: httpx.Client, email: str, password: str, portal_role: str | None = None) -> httpx.Response:
    """Log in and re-store the session cookie without the Secure flag so httpx will
    still send it back over the plain-http localhost connection the test server uses
    (the app sets Secure=true for the real https deployment, which is correct there
    but httpx's cookie jar otherwise withholds it on this http:// test transport)."""
    payload: dict = {"email": email, "password": password}
    if portal_role:
        payload["portal_role"] = portal_role
    response = client.post("/auth/login", json=payload)
    token = response.cookies.get("kiit_session")
    if token:
        client.cookies.clear()
        client.cookies.set("kiit_session", token)
    return response
