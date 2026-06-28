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
    # Active scope this phase: OmniAvatar 1.3B only (ADR-0004).
    assert "omniavatar" in names
    assert "skyreels" not in names  # SkyReels V3 cancelled (ADR-0004)
    assert "multitalk" not in names  # deferred


def test_provider_info_declares_modes():
    omni = create("omniavatar")
    assert isinstance(omni, VideoProvider)
    assert GenerationMode.TALKING_AVATAR in omni.info.modes
    assert omni.supports(GenerationMode.SINGING)


def test_unknown_provider_raises():
    with pytest.raises(KeyError):
        create("does-not-exist")


def test_unsupported_mode_is_rejected_before_model_work():
    # OmniAvatar is audio-driven; it does not advertise TEXT_TO_VIDEO.
    omni = create("omniavatar")
    assert not omni.supports(GenerationMode.TEXT_TO_VIDEO)
    with pytest.raises(UnsupportedModeError):
        omni.generate(None)  # type: ignore[arg-type]


def test_supported_mode_reaches_not_yet_implemented():
    # OmniAvatar advertises TALKING_AVATAR; in design phase it signals clearly.
    omni = create("omniavatar")
    assert omni.supports(GenerationMode.TALKING_AVATAR)
    with pytest.raises(NotYetImplementedError):
        omni.talking_avatar(None)  # type: ignore[arg-type]
