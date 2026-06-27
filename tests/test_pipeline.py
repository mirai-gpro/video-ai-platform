"""Pipeline dispatch tests using a fake Provider (no model, no GPU)."""

from __future__ import annotations

import pytest

from pipeline import Pipeline, PipelineRequest
from providers.base import (
    GenerationMode,
    GenerationRequest,
    GenerationResult,
    ProviderInfo,
    TalkingAvatarRequest,
    VideoProvider,
    VideoSpec,
)


class FakeProvider(VideoProvider):
    @property
    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name="fake",
            model_version="0",
            modes=frozenset({GenerationMode.TEXT_TO_VIDEO}),
        )

    def generate(self, req: GenerationRequest) -> GenerationResult:
        self._require(GenerationMode.TEXT_TO_VIDEO)
        from pathlib import Path

        return GenerationResult(
            output_path=req.output_path or Path("outputs/fake.mp4"),
            provider="fake",
            model_version="0",
            mode=GenerationMode.TEXT_TO_VIDEO,
            spec=req.spec,
            inference_seconds=0.0,
        )


def _pipeline() -> Pipeline:
    return Pipeline(provider_factory=lambda name: FakeProvider())


def test_dispatch_to_supported_mode():
    result = _pipeline().run(
        PipelineRequest(
            provider="fake",
            mode=GenerationMode.TEXT_TO_VIDEO,
            mode_request=GenerationRequest(prompt="hi", spec=VideoSpec()),
        )
    )
    assert result.provider == "fake"


def test_unsupported_mode_rejected():
    with pytest.raises(ValueError):
        _pipeline().run(
            PipelineRequest(
                provider="fake",
                mode=GenerationMode.SINGING,
                mode_request=GenerationRequest(),
            )
        )


def test_wrong_request_type_rejected():
    with pytest.raises(TypeError):
        _pipeline().run(
            PipelineRequest(
                provider="fake",
                mode=GenerationMode.TEXT_TO_VIDEO,
                mode_request=TalkingAvatarRequest(),  # wrong type for mode
            )
        )
