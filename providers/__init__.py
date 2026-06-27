"""Providers package — the only location for model-specific code.

Public surface re-exports the registry helpers and the core contract types so
callers do ``from providers import create, VideoProvider`` without reaching
into submodules.
"""

from providers.base import (
    DialogueRequest,
    ExtendVideoRequest,
    GenerationMode,
    GenerationRequest,
    GenerationResult,
    ProviderError,
    ProviderInfo,
    SingingRequest,
    TalkingAvatarRequest,
    UnsupportedModeError,
    VideoProvider,
    VideoSpec,
)
from providers.registry import available, create, register

__all__ = [
    "DialogueRequest",
    "ExtendVideoRequest",
    "GenerationMode",
    "GenerationRequest",
    "GenerationResult",
    "ProviderError",
    "ProviderInfo",
    "SingingRequest",
    "TalkingAvatarRequest",
    "UnsupportedModeError",
    "VideoProvider",
    "VideoSpec",
    "available",
    "create",
    "register",
]
