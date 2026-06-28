"""API smoke tests — uniform /generate envelope and error mapping."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api import create_app

client = TestClient(create_app())


def test_healthz():
    assert client.get("/healthz").json() == {"status": "ok"}


def test_providers_listed():
    names = {p["name"] for p in client.get("/providers").json()}
    # Active scope this phase: OmniAvatar 1.3B only (ADR-0004).
    assert "omniavatar" in names
    assert "skyreels" not in names


def test_unknown_provider_404():
    r = client.post("/generate", json={"provider": "nope", "mode": "talking_avatar"})
    assert r.status_code == 404


def test_unsupported_mode_400():
    # OmniAvatar is audio-driven; it does not support text_to_video.
    r = client.post("/generate", json={"provider": "omniavatar", "mode": "text_to_video"})
    assert r.status_code == 400


def test_supported_but_unimplemented_501():
    # Design phase: real wiring, model awaits Phase 1 -> 501 Not Implemented.
    r = client.post("/generate", json={"provider": "omniavatar", "mode": "talking_avatar"})
    assert r.status_code == 501
