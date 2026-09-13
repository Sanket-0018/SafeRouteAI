"""
tests/test_bob_brief.py — Unit and integration tests for IBM Bob AI Journey Brief.
"""

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

SAMPLE_BRIEF_PAYLOAD = {
    "route": "Pune → Nagpur",
    "distance_km": 687.9,
    "duration": "8h 17m",
    "departure": "30 Aug 2026 20:00",
    "risk_window": "00:00–03:59",
    "hazards": [
        {
            "type": "ML hotspot",
            "name": "Pune Sector 363",
            "distance_km": 0.2,
            "eta": "20:00",
            "risk_tier": "HIGH"
        },
        {
            "type": "Official blackspot",
            "name": "Loni Kalbhor / Kadamwakvasti Phata",
            "distance_km": 17.4,
            "eta": "20:12",
            "risk_tier": "OFFICIAL_HIGH_SEVERITY"
        }
    ]
}


def test_ai_brief_validation_error():
    """Verify 422 if required fields are missing."""
    resp = client.post("/api/journey/ai-brief", json={"route": "Pune → Mumbai"})
    assert resp.status_code == 422


@patch("src.journey.bob_service.requests.post")
@patch("src.journey.bob_service.get_bob_api_key", return_value="test-secret-key-xyz")
def test_ai_brief_success_mocked(mock_key, mock_post):
    """Verify successful response when IBM Bob responds with 200."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "role": "assistant",
                    "content": (
                        "• Primary risk window: 00:00–03:59 with elevated night transit density.\n"
                        "• Pune Sector 363 flagged by ML model at 20:00.\n"
                        "• Official blackspot at Loni Kalbhor (17.4 km, ETA 20:12).\n"
                        "• Maintain safe following distance and plan rest stops before midnight."
                    )
                }
            }
        ]
    }
    mock_post.return_value = mock_resp

    resp = client.post("/api/journey/ai-brief", json=SAMPLE_BRIEF_PAYLOAD)
    assert resp.status_code == 200
    data = resp.json()
    assert "brief" in data
    assert "Pune Sector 363" in data["brief"]
    assert "model" in data
    assert "disclaimer" in data
    assert "does not guarantee safety" in data["disclaimer"]

    # Verify alias endpoint also works
    resp_alias = client.post("/journey/ai-brief", json=SAMPLE_BRIEF_PAYLOAD)
    assert resp_alias.status_code == 200


@patch("src.journey.bob_service.get_bob_api_key", return_value=None)
def test_ai_brief_missing_api_key(mock_key):
    """Verify 503 response if BOB_API_KEY is not configured."""
    resp = client.post("/api/journey/ai-brief", json=SAMPLE_BRIEF_PAYLOAD)
    assert resp.status_code == 503
    assert "BOB_API_KEY" in resp.json()["detail"]


@patch("src.journey.bob_service.requests.post")
@patch("src.journey.bob_service.get_bob_api_key", return_value="test-secret-key-xyz")
def test_ai_brief_gateway_auth_failure(mock_key, mock_post):
    """Verify 502 without credential leakage on Bob auth failure."""
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.text = '{"error": "unauthorized"}'
    mock_post.return_value = mock_resp

    resp = client.post("/api/journey/ai-brief", json=SAMPLE_BRIEF_PAYLOAD)
    assert resp.status_code == 502
    assert "test-secret-key-xyz" not in resp.text


@patch("src.journey.bob_service.requests.post")
@patch("src.journey.bob_service.get_bob_api_key", return_value="test-secret-key-xyz")
def test_ai_brief_strict_evidence_prompt(mock_key, mock_post):
    """Verify that system prompt enforces strict evidence grounding and forbids hallucinations."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "role": "assistant",
                    "content": "• Risk window: 00:00–03:59.\n• ML hotspot: Pune Sector 363.\n• Official blackspot: Loni Kalbhor.\n• General precaution: Maintain safe distance."
                }
            }
        ]
    }
    mock_post.return_value = mock_resp

    resp = client.post("/api/journey/ai-brief", json=SAMPLE_BRIEF_PAYLOAD)
    assert resp.status_code == 200

    # Inspect call arguments to requests.post
    assert mock_post.called
    call_kwargs = mock_post.call_args[1]
    sent_payload = call_kwargs["json"]
    system_msg = next(m["content"] for m in sent_payload["messages"] if m["role"] == "system")

    # Assert strict evidence grounding constraints are enforced in the prompt
    assert "STRICT EVIDENCE-GROUNDING RULES" in system_msg
    assert "Do NOT invent weather" in system_msg
    assert "Do NOT invent visibility" in system_msg
    assert "Do NOT invent driver fatigue" in system_msg
    assert "Do NOT invent enforcement" in system_msg
    assert "NEVER refer to an ML-predicted hotspot as an officially designated blackspot" in system_msg
    assert "Return only complete bullets. If there is not enough output space to complete another bullet, omit that bullet entirely." in system_msg
    assert "target 4 to 5 bullet points" in system_msg


@patch("src.journey.bob_service.requests.post")
@patch("src.journey.bob_service.get_bob_api_key", return_value="test-secret-key-xyz")
def test_ai_brief_truncation_omits_incomplete_bullet(mock_key, mock_post):
    """Verify that response handling omits a trailing truncated bullet that was cut off."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [
            {
                "finish_reason": "length",
                "message": {
                    "role": "assistant",
                    "content": (
                        "• Route: Pune → Latur | 322.3 km | 3h 54m.\n"
                        "• Departure: 20:00, 30 Aug 2026.\n"
                        "• Night-window travel: The journey falls within the supplied 20:00–23:59 historical risk window.\n"
                        "• ML Hotspot: Pune Sector 363 — approximately 4.5 km from the journey start.\n"
                        "• Cluster Density Warning: All six flagged hazards are concentrated"
                    )
                }
            }
        ]
    }
    mock_post.return_value = mock_resp

    resp = client.post("/api/journey/ai-brief", json=SAMPLE_BRIEF_PAYLOAD)
    assert resp.status_code == 200
    data = resp.json()
    brief = data["brief"]

    # Incomplete sentence should be safely omitted
    assert "Cluster Density Warning: All six flagged hazards are concentrated" not in brief
    # Complete sentences must remain
    assert "Pune Sector 363" in brief
    # The brief must end at a complete sentence
    assert brief.endswith(".")

