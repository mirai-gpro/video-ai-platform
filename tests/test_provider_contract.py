"""Contract tests for the Provider abstraction and registry.

These verify the *design* holds without any model: capability declaration,
mode dispatch, registry resolution, and the design-phase "not yet implemented"
behavior. They run on CPU-only CI.
"""

from __future__ import annotations

import pytest

from providers import GenerationMode, available, create
from providers.base import (
    NotYetImplementedError,
    UnsupportedModeError,
    VideoProvider,
)


def test_builtin_providers_registered():
    names = available()
    assert "skyreels" in names
    assert "multitalk" in names


def test_provider_info_declares_modes():
    sky = create("skyreels")
    assert isinstance(sky, VideoProvider)
    assert GenerationMode.TEXT_TO_VIDEO in sky.info.modes
    assert sky.supports(GenerationMode.TEXT_TO_VIDEO)


def test_unknown_provider_raises():
    with pytest.raises(KeyError):
        create("does-not-exist")


def test_unsupported_mode_is_rejected_before_model_work():
    # SkyReels does not advertise SINGING -> capability guard fires.
    sky = create("skyreels")
    assert not sky.supports(GenerationMode.SINGING)
    with pytest.raises(UnsupportedModeError):
        sky.singing(None)  # type: ignore[arg-type]


def test_supported_mode_reaches_not_yet_implemented():
    # MultiTalk advertises DIALOGUE; in design phase it signals clearly.
    mt = create("multitalk")
    assert mt.supports(GenerationMode.DIALOGUE)
    with pytest.raises(NotYetImplementedError):
        mt.dialogue(None)  # type: ignore[arg-type]
