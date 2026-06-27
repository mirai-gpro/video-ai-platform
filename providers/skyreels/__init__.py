"""SkyReels V3 Provider.

Wraps the upstream ``third_party/SkyReels-V3`` submodule behind the common
``VideoProvider`` contract. Per policy, NO upstream code is modified; this
package adapts upstream into our request/result types and is the only place
SkyReels-specific concepts may appear.

Design-phase status: capabilities are declared and the wiring is registered,
but the generation methods raise ``NotYetImplementedError`` until model
integration is approved (Phase 1).
"""

from __future__ import annotations

from providers.base import (
    GenerationMode,
    GenerationRequest,
    GenerationResult,
    NotYetImplementedError,
    ProviderInfo,
    TalkingAvatarRequest,
    VideoProvider,
)


class SkyReelsProvider(VideoProvider):
    """SkyReels V3 adapter (text-to-video + talking avatar at launch)."""

    @property
    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name="skyreels",
            model_version="V3",
            modes=frozenset(
                {
                    GenerationMode.TEXT_TO_VIDEO,
                    GenerationMode.TALKING_AVATAR,
                    GenerationMode.EXTEND_VIDEO,
                }
            ),
            description="SkyReels V3 — high-quality text-to-video foundation model.",
        )

    def generate(self, req: GenerationRequest) -> GenerationResult:
        self._require(GenerationMode.TEXT_TO_VIDEO)
        raise NotYetImplementedError(
            "SkyReels.generate awaits Phase 1 integration (design approval pending)."
        )

    def talking_avatar(self, req: TalkingAvatarRequest) -> GenerationResult:
        self._require(GenerationMode.TALKING_AVATAR)
        raise NotYetImplementedError(
            "SkyReels.talking_avatar awaits Phase 1 integration."
        )


def register_provider() -> None:
    from providers.registry import register

    register("skyreels", SkyReelsProvider)
