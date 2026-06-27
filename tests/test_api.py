"""API smoke tests — uniform /generate envelope and error mapping."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api import create_app

client = TestClient(create_app())


def test_healthz():
    assert client.get("/healthz").json() == {"status": "ok"}


def test_providers_listed():
    names = {p["name"] for p in client.get("/providers").json()}
    assert {"skyreels", "multitalk"} <= names


def test_unknown_provider_404():
    r = client.post("/generate", json={"provider": "nope", "mode": "text_to_video"})
    assert r.status_code == 404


def test_unsupported_mode_400():
    # SkyReels does not support singing.
    r = client.post("/generate", json={"provider": "skyreels", "mode": "singing"})
    assert r.status_code == 400


def test_supported_but_unimplemented_501():
    # Design phase: real wiring, model awaits approval -> 501 Not Implemented.
    r = client.post("/generate", json={"provider": "skyreels", "mode": "text_to_video"})
    assert r.status_code == 501
