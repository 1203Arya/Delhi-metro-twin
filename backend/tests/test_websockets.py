from __future__ import annotations

from starlette.testclient import TestClient

from app.main import create_app


def test_websocket_simulation() -> None:
    app = create_app()
    client = TestClient(app)
    with client.websocket_connect("/api/v1/ws/simulation") as ws:
        data = ws.receive_json()
        assert data["type"] == "position_update"
        assert "trains" in data
