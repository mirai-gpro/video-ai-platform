"""Pipeline: model-agnostic dispatch from request to Provider call.

Flow (proposal §9):

    PipelineRequest -> Pipeline -> Provider -> (SkyReels | future models | …)

The Pipeline knows about modes and Providers in the abstract only. It does not
know that SkyReels uses diffusion or that an audio-driven model consumes audio
tracks — that knowledge lives entirely behind the Provider boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from providers import GenerationResult, VideoProvider, create
from providers.base import (
    DialogueRequest,
    ExtendVideoRequest,
    GenerationMode,
    GenerationRequest,
    SingingRequest,
    TalkingAvatarRequest,
    _BaseRequest,
)


@dataclass
class PipelineRequest:
    """A fully-resolved unit of work: which Provider, which mode, which inputs.

    ``mode_request`` is one of the concrete request dataclasses from
    ``providers.base`` matching ``mode``. The API/CLI build this; the Pipeline
    only dispatches it.
    """

    provider: str
    mode: GenerationMode
    mode_request: _BaseRequest = field(default_factory=_BaseRequest)


# Mode -> the Provider method that serves it. Adding a mode is a one-line
# change here plus the contract in providers.base — no model edits.
_DISPATCH: dict[GenerationMode, str] = {
    GenerationMode.TEXT_TO_VIDEO: "generate",
    GenerationMode.TALKING_AVATAR: "talking_avatar",
    GenerationMode.DIALOGUE: "dialogue",
    GenerationMode.SINGING: "singing",
    GenerationMode.EXTEND_VIDEO: "extend_video",
}

_EXPECTED_REQUEST: dict[GenerationMode, type] = {
    GenerationMode.TEXT_TO_VIDEO: GenerationRequest,
    GenerationMode.TALKING_AVATAR: TalkingAvatarRequest,
    GenerationMode.DIALOGUE: DialogueRequest,
    GenerationMode.SINGING: SingingRequest,
    GenerationMode.EXTEND_VIDEO: ExtendVideoRequest,
}


class Pipeline:
    """Resolves a Provider and dispatches a request to the correct method."""

    def __init__(self, provider_factory=create) -> None:
        # Injectable for tests; defaults to the real registry resolver.
        self._provider_factory = provider_factory

    def run(self, request: PipelineRequest) -> GenerationResult:
        provider: VideoProvider = self._provider_factory(request.provider)

        if not provider.supports(request.mode):
            raise ValueError(
                f"Provider '{request.provider}' does not support mode "
                f"'{request.mode.value}'."
            )

        expected = _EXPECTED_REQUEST[request.mode]
        if not isinstance(request.mode_request, expected):
            raise TypeError(
                f"Mode '{request.mode.value}' expects a {expected.__name__}, got "
                f"{type(request.mode_request).__name__}."
            )

        method = getattr(provider, _DISPATCH[request.mode])
        # Phase 3: wrap this call in benchmarks.capture(...) to record metrics.
        return method(request.mode_request)
