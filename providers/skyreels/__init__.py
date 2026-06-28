"""SkyReels V3 Provider.

Wraps the upstream ``third_party/SkyReels-V3`` submodule
(github.com/SkyworkAI/SkyReels-V3) behind the common ``VideoProvider``
contract. Per policy, NO upstream code is modified; this package is the only
place SkyReels-specific concepts may appear.

Integration status (Phase 1, in progress):
  * The capability declaration, option handling, request→work flow, and result
    shape are implemented here.
  * The two points that require the upstream code to be present — model
    loading and the actual inference call — are marked ``# PHASE 1`` and raise
    ``NotYetImplementedError`` until the submodule is materialized in a
    GitHub-reachable environment (ADR-0002) and its public API is wired in.

The Pipeline measures resources around the call and records the benchmark
(``benchmarks.recorder``); this Provider only needs to return a populated
``GenerationResult`` (it may also report model-specific knobs in ``metrics``).
"""

from __future__ import annotations

from typing import Any

from providers.base import (
    ExtendVideoRequest,
    GenerationMode,
    GenerationRequest,
    GenerationResult,
    NotYetImplementedError,
    ProviderInfo,
    TalkingAvatarRequest,
    VideoProvider,
    _BaseRequest,
)


class SkyReelsProvider(VideoProvider):
    """SkyReels V3 adapter (text-to-video, talking avatar, video extension)."""

    def __init__(self, options: dict[str, Any] | None = None) -> None:
        # Per-provider options (weights_path, dtype, attention, cpu_offload, …).
        # Passed through from config and interpreted only here. Resolved lazily
        # so importing/registering the Provider never reads config or CUDA.
        self._options = options
        self._model: Any | None = None  # upstream pipeline, loaded on first use

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

    # --- options -----------------------------------------------------------

    def _resolve_options(self) -> dict[str, Any]:
        if self._options is not None:
            return self._options
        try:
            from config import load_settings

            self._options = load_settings().providers.options.get("skyreels", {})
        except Exception:  # noqa: BLE001 - missing/oddly-shaped config -> defaults
            self._options = {}
        return self._options

    # --- model lifecycle ---------------------------------------------------

    def _ensure_model(self) -> Any:
        """Load the upstream SkyReels V3 pipeline once, then reuse it (warm)."""
        if self._model is not None:
            return self._model
        opts = self._resolve_options()
        # PHASE 1: instantiate the upstream pipeline from third_party/SkyReels-V3
        # using these options once the submodule is present and its public API
        # is confirmed (ADR-0002):
        #   weights_path = opts.get("weights_path")
        #   dtype        = opts.get("dtype", "bfloat16")
        #   attention    = opts.get("attention", "flash")   # flash|sage|sdpa
        #   cpu_offload  = opts.get("cpu_offload", False)    # fit 24GB RTX 4090
        #   from <upstream module> import <pipeline class>
        #   self._model = <pipeline class>.from_pretrained(weights_path, ...)
        raise NotYetImplementedError(
            "SkyReels V3 model loading is wired in Phase 1, once the submodule "
            "(third_party/SkyReels-V3) is materialized and its inference API is "
            f"confirmed. Resolved options keys: {sorted(opts)} (ADR-0002)."
        )

    # --- capability methods ------------------------------------------------

    def generate(self, req: GenerationRequest) -> GenerationResult:
        self._require(GenerationMode.TEXT_TO_VIDEO)
        return self._run(GenerationMode.TEXT_TO_VIDEO, req)

    def talking_avatar(self, req: TalkingAvatarRequest) -> GenerationResult:
        self._require(GenerationMode.TALKING_AVATAR)
        return self._run(GenerationMode.TALKING_AVATAR, req)

    def extend_video(self, req: ExtendVideoRequest) -> GenerationResult:
        self._require(GenerationMode.EXTEND_VIDEO)
        return self._run(GenerationMode.EXTEND_VIDEO, req)

    # --- shared run path ---------------------------------------------------

    def _run(self, mode: GenerationMode, req: _BaseRequest) -> GenerationResult:
        """Translate request → upstream call → GenerationResult.

        The skeleton documents the Phase-1 flow; ``_ensure_model`` raises until
        the upstream API is wired, so the steps below are unreachable for now.
        """
        self._ensure_model()  # raises NotYetImplementedError in the current phase
        # PHASE 1 flow (implemented once the upstream API is known):
        #   1. map `req` (prompt / spec / mode inputs / req.extra) to upstream kwargs
        #   2. run inference -> frames/tensor, timing it (perf_counter)
        #   3. encode/write the video to `req.output_path`
        #   4. return GenerationResult(output_path=..., provider="skyreels",
        #        model_version="V3", mode=mode, spec=req.spec,
        #        inference_seconds=<measured>, metrics={"steps":..., "seed":...})
        raise NotYetImplementedError(
            f"SkyReels V3 '{mode.value}' generation awaits Phase 1 integration."
        )


def register_provider() -> None:
    from providers.registry import register

    register("skyreels", SkyReelsProvider)
