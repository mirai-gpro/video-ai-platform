"""MultiTalk Provider.

Wraps the upstream ``third_party/MultiTalk`` submodule behind the common
``VideoProvider`` contract. MultiTalk's strength is audio-driven multi-person
dialogue and singing lip-sync (validated previously on GCP L4). No upstream
code is modified; all adaptation lives here.

Design-phase status: capabilities declared, methods raise
``NotYetImplementedError`` until Phase 1.
"""

from __future__ import annotations

from providers.base import (
    DialogueRequest,
    GenerationMode,
    GenerationResult,
    NotYetImplementedError,
    ProviderInfo,
    SingingRequest,
    TalkingAvatarRequest,
    VideoProvider,
)


class MultiTalkProvider(VideoProvider):
    """MultiTalk adapter (talking avatar, dialogue, singing)."""

    @property
    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name="multitalk",
            model_version="validated-l4-baseline",
            modes=frozenset(
                {
                    GenerationMode.TALKING_AVATAR,
                    GenerationMode.DIALOGUE,
                    GenerationMode.SINGING,
                }
            ),
            description="MultiTalk — audio-driven multi-person dialogue & singing lip-sync.",
        )

    def talking_avatar(self, req: TalkingAvatarRequest) -> GenerationResult:
        self._require(GenerationMode.TALKING_AVATAR)
        raise NotYetImplementedError("MultiTalk.talking_avatar awaits Phase 1 integration.")

    def dialogue(self, req: DialogueRequest) -> GenerationResult:
        self._require(GenerationMode.DIALOGUE)
        raise NotYetImplementedError("MultiTalk.dialogue awaits Phase 1 integration.")

    def singing(self, req: SingingRequest) -> GenerationResult:
        self._require(GenerationMode.SINGING)
        raise NotYetImplementedError("MultiTalk.singing awaits Phase 1 integration.")


def register_provider() -> None:
    from providers.registry import register

    register("multitalk", MultiTalkProvider)
