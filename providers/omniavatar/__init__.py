"""OmniAvatar 1.3B Provider.

Wraps the upstream ``third_party/OmniAvatar`` submodule
(github.com/Omni-Avatar/OmniAvatar, Apache-2.0) behind the common
``VideoProvider`` contract. OmniAvatar is an audio-driven avatar video model
(lip-sync + adaptive body animation, single person) built on Wan2.1-T2V-1.3B.
The 1.3B variant is chosen to fit the 24 GB RTX 4090 dev GPU (ADR-0004).

Per policy, NO upstream code is modified; this package is the only place
OmniAvatar-specific concepts may appear.

Integration status (Phase 1, in progress):
  * Capability declaration, option handling, the warm-model lifecycle, and the
    request→work→result flow are implemented here.
  * The upstream-dependent points — model loading and the inference call — are
    marked ``# PHASE 1`` and raise ``NotYetImplementedError`` until the
    submodule is materialized (ADR-0002) and its API is wired in.

Upstream specifics (for the Phase-1 wiring):
  * Entry point: ``scripts/inference.py`` with ``configs/inference_1.3B.yaml``.
  * Input line format: ``"[prompt]@@[img_path]@@[audio_path]"``.
  * Key knobs: ``guidance_scale``, ``audio_scale``, ``num_steps`` (20-50).
  * Weights (HuggingFace): ``OmniAvatar/OmniAvatar-1.3B``,
    ``Wan-AI/Wan2.1-T2V-1.3B``, ``facebook/wav2vec2-base-960h``.
"""

from __future__ import annotations

from typing import Any

from providers.base import (
    GenerationMode,
    GenerationResult,
    NotYetImplementedError,
    ProviderInfo,
    SingingRequest,
    TalkingAvatarRequest,
    VideoProvider,
    _BaseRequest,
)


class OmniAvatarProvider(VideoProvider):
    """OmniAvatar 1.3B adapter (audio-driven talking avatar + singing)."""

    def __init__(self, options: dict[str, Any] | None = None) -> None:
        # Per-provider options (weights_path, num_steps, guidance_scale,
        # audio_scale, dtype, cpu_offload, flash_attn, …). Passed through from
        # config and interpreted only here. Resolved lazily so importing the
        # Provider never reads config or CUDA.
        self._options = options
        self._model: Any | None = None  # upstream pipeline, loaded on first use

    @property
    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name="omniavatar",
            model_version="1.3B",
            modes=frozenset(
                {
                    GenerationMode.TALKING_AVATAR,
                    GenerationMode.SINGING,
                }
            ),
            description=(
                "OmniAvatar 1.3B — audio-driven avatar video with lip-sync and "
                "adaptive body animation (Wan2.1-T2V-1.3B base, Apache-2.0)."
            ),
        )

    # --- options -----------------------------------------------------------

    def _resolve_options(self) -> dict[str, Any]:
        if self._options is not None:
            return self._options
        try:
            from config import load_settings

            self._options = load_settings().providers.options.get("omniavatar", {})
        except Exception:  # noqa: BLE001 - missing/oddly-shaped config -> defaults
            self._options = {}
        return self._options

    # --- model lifecycle ---------------------------------------------------

    def _ensure_model(self) -> Any:
        """Load the upstream OmniAvatar pipeline once, then reuse it (warm)."""
        if self._model is not None:
            return self._model
        opts = self._resolve_options()
        # PHASE 1: build the upstream OmniAvatar 1.3B pipeline from
        # third_party/OmniAvatar using these options once the submodule is
        # present and its API is confirmed (ADR-0002):
        #   weights_path  = opts.get("weights_path")      # OmniAvatar/OmniAvatar-1.3B
        #   config_yaml   = opts.get("config", "configs/inference_1.3B.yaml")
        #   num_steps     = opts.get("num_steps", 25)      # 20-50
        #   guidance_scale= opts.get("guidance_scale")
        #   audio_scale   = opts.get("audio_scale")
        #   dtype         = opts.get("dtype", "bfloat16")
        #   cpu_offload   = opts.get("cpu_offload", False) # fit 24GB RTX 4090
        #   flash_attn    = opts.get("flash_attn", True)
        raise NotYetImplementedError(
            "OmniAvatar 1.3B model loading is wired in Phase 1, once the submodule "
            "(third_party/OmniAvatar) is materialized and its inference API is "
            f"confirmed. Resolved options keys: {sorted(opts)} (ADR-0002)."
        )

    # --- capability methods ------------------------------------------------

    def talking_avatar(self, req: TalkingAvatarRequest) -> GenerationResult:
        self._require(GenerationMode.TALKING_AVATAR)
        return self._run(GenerationMode.TALKING_AVATAR, req)

    def singing(self, req: SingingRequest) -> GenerationResult:
        self._require(GenerationMode.SINGING)
        return self._run(GenerationMode.SINGING, req)

    # --- shared run path ---------------------------------------------------

    def _run(self, mode: GenerationMode, req: _BaseRequest) -> GenerationResult:
        """Translate request → upstream call → GenerationResult.

        The skeleton documents the Phase-1 flow; ``_ensure_model`` raises until
        the upstream API is wired, so the steps below are unreachable for now.
        """
        self._ensure_model()  # raises NotYetImplementedError in the current phase
        # PHASE 1 flow (implemented once the upstream API is known):
        #   1. build the input line "[prompt]@@[img_path]@@[audio_path]" from
        #      req.prompt, req.reference_image, req.audio
        #   2. run inference (num_steps / guidance_scale / audio_scale), timing it
        #   3. write the avatar video to req.output_path
        #   4. return GenerationResult(output_path=..., provider="omniavatar",
        #        model_version="1.3B", mode=mode, spec=req.spec,
        #        inference_seconds=<measured>,
        #        metrics={"num_steps":..., "guidance_scale":..., "audio_scale":...})
        raise NotYetImplementedError(
            f"OmniAvatar 1.3B '{mode.value}' generation awaits Phase 1 integration."
        )


def register_provider() -> None:
    from providers.registry import register

    register("omniavatar", OmniAvatarProvider)
