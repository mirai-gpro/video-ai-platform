"""Provider abstraction — the single contract every video model implements.

This module is the architectural keystone of the platform. The Pipeline, REST
API, and CLI depend ONLY on the types defined here; they never import a
model-specific package. Adding a new model (SkyReels V4, Wan, Hallo2,
FaceFusion, …) means writing a new ``VideoProvider`` subclass under
``providers/<name>/`` and registering it — nothing upstream of the Provider
boundary changes.

Design rules enforced by this contract:
  * Requests and results are plain, serializable data classes so they cross
    the REST/CLI boundary unchanged and are reproducible in benchmarks.
  * A Provider declares its capabilities; the Pipeline validates a request
    against them before doing any work, yielding clear errors instead of
    deep model-specific tracebacks.
  * No model-specific concept (checkpoint names, sampler kwargs, …) leaks
    into the shared types. Model-specific knobs ride along in
    ``GenerationRequest.extra`` and are interpreted only inside the Provider.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class GenerationMode(StrEnum):
    """The product-level capabilities a Provider may support.

    These map 1:1 to the abstract methods below and to the REST ``mode``
    field. Kept as a closed enum so the API can validate ``mode`` without
    importing any Provider.
    """

    TEXT_TO_VIDEO = "text_to_video"
    TALKING_AVATAR = "talking_avatar"
    DIALOGUE = "dialogue"
    SINGING = "singing"
    EXTEND_VIDEO = "extend_video"


@dataclass(frozen=True)
class ProviderInfo:
    """Static identity/metadata of a Provider, surfaced in benchmark records."""

    name: str
    model_version: str
    modes: frozenset[GenerationMode]
    description: str = ""


@dataclass
class VideoSpec:
    """Output video parameters shared by every mode."""

    width: int = 1280
    height: int = 720
    fps: int = 24
    duration_seconds: float = 15.0
    seed: int | None = None


@dataclass
class _BaseRequest:
    """Fields common to all requests.

    ``output_path`` is where the Provider must write the rendered file.
    ``extra`` carries model-specific options that the shared layers pass
    through verbatim and never interpret.
    """

    spec: VideoSpec = field(default_factory=VideoSpec)
    output_path: Path | None = None
    extra: dict[str, object] = field(default_factory=dict)


@dataclass
class GenerationRequest(_BaseRequest):
    """Text/image conditioned text-to-video generation."""

    prompt: str = ""
    negative_prompt: str = ""
    reference_image: Path | None = None


@dataclass
class TalkingAvatarRequest(_BaseRequest):
    """Single-speaker talking-head driven by a reference image + audio."""

    reference_image: Path | None = None
    audio: Path | None = None
    prompt: str = ""


@dataclass
class SingingRequest(_BaseRequest):
    """Singing / lip-sync performance driven by a vocal track."""

    reference_image: Path | None = None
    audio: Path | None = None
    prompt: str = ""


@dataclass
class DialogueRequest(_BaseRequest):
    """Multi-speaker conversation (e.g. MultiTalk two-person dialogue)."""

    # One entry per speaker; each pairs a reference image with that speaker's
    # audio track. Order defines speaker index.
    speakers: list[dict[str, Path]] = field(default_factory=list)
    prompt: str = ""


@dataclass
class ExtendVideoRequest(_BaseRequest):
    """Continue an existing clip to a longer duration."""

    source_video: Path | None = None
    prompt: str = ""


@dataclass
class GenerationResult:
    """Uniform result returned by every Provider method.

    ``metrics`` is intentionally free-form so a Provider can attach whatever
    it measured (peak VRAM, step timings, …); the benchmark layer reads the
    well-known keys and stores the rest as opaque settings.
    """

    output_path: Path
    provider: str
    model_version: str
    mode: GenerationMode
    spec: VideoSpec
    inference_seconds: float
    metrics: dict[str, object] = field(default_factory=dict)


class ProviderError(RuntimeError):
    """Base class for provider-layer failures."""


class UnsupportedModeError(ProviderError):
    """Raised when a request targets a mode the Provider does not implement."""


class NotYetImplementedError(ProviderError):
    """Design-phase marker: wiring exists, model integration awaits approval."""


class VideoProvider(ABC):
    """Common interface implemented by every video generation model.

    Subclasses live under ``providers/<name>/`` and are the ONLY place
    model-specific code is permitted. The default method bodies raise
    :class:`UnsupportedModeError`; a Provider overrides exactly the modes it
    advertises in :attr:`info`.
    """

    @property
    @abstractmethod
    def info(self) -> ProviderInfo:
        """Identity, version, and supported modes for this Provider."""

    def supports(self, mode: GenerationMode) -> bool:
        return mode in self.info.modes

    def _require(self, mode: GenerationMode) -> None:
        if not self.supports(mode):
            raise UnsupportedModeError(
                f"Provider '{self.info.name}' does not support mode '{mode.value}'. "
                f"Supported: {sorted(m.value for m in self.info.modes)}"
            )

    # --- Capability methods (proposal §8) ---------------------------------
    # Each guards on capability, then defers to the model-specific override.

    def generate(self, req: GenerationRequest) -> GenerationResult:
        self._require(GenerationMode.TEXT_TO_VIDEO)
        raise UnsupportedModeError(self._not_overridden("generate"))

    def talking_avatar(self, req: TalkingAvatarRequest) -> GenerationResult:
        self._require(GenerationMode.TALKING_AVATAR)
        raise UnsupportedModeError(self._not_overridden("talking_avatar"))

    def dialogue(self, req: DialogueRequest) -> GenerationResult:
        self._require(GenerationMode.DIALOGUE)
        raise UnsupportedModeError(self._not_overridden("dialogue"))

    def singing(self, req: SingingRequest) -> GenerationResult:
        self._require(GenerationMode.SINGING)
        raise UnsupportedModeError(self._not_overridden("singing"))

    def extend_video(self, req: ExtendVideoRequest) -> GenerationResult:
        self._require(GenerationMode.EXTEND_VIDEO)
        raise UnsupportedModeError(self._not_overridden("extend_video"))

    def _not_overridden(self, method: str) -> str:
        return (
            f"Provider '{self.info.name}' advertises a mode but did not override "
            f"'{method}()'."
        )
