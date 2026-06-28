"""Pipeline: model-agnostic dispatch from request to Provider call.

Flow (proposal §9):

    PipelineRequest -> Pipeline -> Provider -> (OmniAvatar | future models | …)

The Pipeline knows about modes and Providers in the abstract only. It does not
know that OmniAvatar is audio-driven or that another model uses pure diffusion
— that knowledge lives entirely behind the Provider boundary.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from benchmarks.capture import measure
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

if TYPE_CHECKING:
    from benchmarks.recorder import BenchmarkRecorder
    from config import Settings


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

    def __init__(
        self,
        provider_factory=create,
        recorder: BenchmarkRecorder | None = None,
    ) -> None:
        # Injectable for tests; defaults to the real registry resolver.
        self._provider_factory = provider_factory
        # Optional benchmark recorder; when set, successful runs are measured
        # and persisted. Left None keeps the Pipeline a pure dispatcher.
        self._recorder = recorder

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

        if self._recorder is None:
            return method(request.mode_request)

        # Measure around the call; on failure the exception propagates and no
        # record is written (benchmarks reflect successful generations only).
        with measure() as sample:
            result = method(request.mode_request)
        self._recorder.record(result, sample)
        return result


def build_pipeline(settings: Settings | None = None) -> Pipeline:
    """Composition root: a Pipeline wired with a benchmark recorder per config.

    Used by the API and CLI so real Phase-1 runs auto-record benchmarks. Unit
    tests construct ``Pipeline`` directly (no recorder) for pure dispatch.
    """
    from config import load_settings

    settings = settings or load_settings()
    recorder = None
    if settings.benchmark.enabled:
        from benchmarks.recorder import BenchmarkRecorder

        recorder = BenchmarkRecorder(settings.benchmark.output_dir, enabled=True)
    return Pipeline(recorder=recorder)
