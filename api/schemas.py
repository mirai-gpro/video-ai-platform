"""Pydantic request/response models for the REST API.

These mirror the provider contract but are HTTP-facing (validation, JSON
shapes). The API layer maps them onto ``providers.base`` dataclasses before
handing off to the Pipeline, so the wire format and the internal contract can
evolve independently.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from providers.base import GenerationMode


class VideoSpecModel(BaseModel):
    width: int = 1280
    height: int = 720
    fps: int = 24
    duration_seconds: float = 15.0
    seed: int | None = None


class GenerateRequestModel(BaseModel):
    """Body for ``POST /generate`` (proposal §10).

    The same envelope serves every model and mode; model-specific knobs go in
    ``extra`` and are passed through untouched.
    """

    provider: str = Field(..., examples=["skyreels"])
    mode: GenerationMode = Field(..., examples=["text_to_video", "talking_avatar"])
    prompt: str = ""
    negative_prompt: str = ""
    reference_image: str | None = None
    audio: str | None = None
    source_video: str | None = None
    speakers: list[dict[str, str]] = Field(default_factory=list)
    spec: VideoSpecModel = Field(default_factory=VideoSpecModel)
    extra: dict[str, object] = Field(default_factory=dict)


class GenerateResponseModel(BaseModel):
    provider: str
    model_version: str
    mode: GenerationMode
    output_path: str
    inference_seconds: float
    metrics: dict[str, object] = Field(default_factory=dict)


class ProviderInfoModel(BaseModel):
    name: str
    model_version: str
    modes: list[GenerationMode]
    description: str
