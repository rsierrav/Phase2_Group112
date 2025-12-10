from fastapi.testclient import TestClient
from backend.backend.app.main import app


client = TestClient(app)

ALLOWED_TRACKS = {
    "Performance track",
    "Access control track",
    "High assurance track",
    "Other Security track",
}


def test_tracks_returns_expected_structure():
    response = client.get("/tracks")
    assert response.status_code == 200

    body = response.json()
    assert "plannedTracks" in body
    assert isinstance(body["plannedTracks"], list)

    # Team only implements Performance track
    assert body["plannedTracks"] == ["Performance track"]

    # Validate values belong to the allowed enum
    for t in body["plannedTracks"]:
        assert t in ALLOWED_TRACKS
