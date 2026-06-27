"""FastAPI application factory.

Exposes the uniform ``POST /generate`` plus discovery endpoints. The handler
is deliberately thin: validate -> build the typed request -> Pipeline.run ->
shape the response. No model knowledge lives here.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException

from api.schemas import (
    GenerateRequestModel,
    GenerateResponseModel,
    ProviderInfoModel,
)
from pipeline import Pipeline, PipelineRequest
from providers import available, create
from providers.base import (
    DialogueRequest,
    ExtendVideoRequest,
    GenerationMode,
    GenerationRequest,
    ProviderError,
    SingingRequest,
    TalkingAvatarRequest,
    VideoSpec,
    _BaseRequest,
)


def _to_path(value: str | None) -> Path | None:
    return Path(value) if value else None


def _build_mode_request(body: GenerateRequestModel) -> _BaseRequest:
    """Map the HTTP body onto the typed request for the chosen mode."""
    spec = VideoSpec(**body.spec.model_dump())
    common = {"spec": spec, "extra": body.extra}

    match body.mode:
        case GenerationMode.TEXT_TO_VIDEO:
            return GenerationRequest(
                prompt=body.prompt,
                negative_prompt=body.negative_prompt,
                reference_image=_to_path(body.reference_image),
                **common,
            )
        case GenerationMode.TALKING_AVATAR:
            return TalkingAvatarRequest(
                reference_image=_to_path(body.reference_image),
                audio=_to_path(body.audio),
                prompt=body.prompt,
                **common,
            )
        case GenerationMode.SINGING:
            return SingingRequest(
                reference_image=_to_path(body.reference_image),
                audio=_to_path(body.audio),
                prompt=body.prompt,
                **common,
            )
        case GenerationMode.DIALOGUE:
            speakers = [{k: Path(v) for k, v in s.items()} for s in body.speakers]
            return DialogueRequest(speakers=speakers, prompt=body.prompt, **common)
        case GenerationMode.EXTEND_VIDEO:
            return ExtendVideoRequest(
                source_video=_to_path(body.source_video),
                prompt=body.prompt,
                **common,
            )
    raise HTTPException(status_code=422, detail=f"Unhandled mode '{body.mode}'.")


def create_app(pipeline: Pipeline | None = None) -> FastAPI:
    app = FastAPI(
        title="Video AI Platform",
        version="0.1.0",
        summary="Model-agnostic video generation API.",
    )
    pipe = pipeline or Pipeline()

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/providers", response_model=list[ProviderInfoModel])
    def list_providers() -> list[ProviderInfoModel]:
        infos = []
        for name in available():
            info = create(name).info
            infos.append(
                ProviderInfoModel(
                    name=info.name,
                    model_version=info.model_version,
                    modes=sorted(info.modes, key=lambda m: m.value),
                    description=info.description,
                )
            )
        return infos

    @app.post("/generate", response_model=GenerateResponseModel)
    def generate(body: GenerateRequestModel) -> GenerateResponseModel:
        try:
            req = PipelineRequest(
                provider=body.provider,
                mode=body.mode,
                mode_request=_build_mode_request(body),
            )
            result = pipe.run(req)
        except KeyError as e:  # unknown provider
            raise HTTPException(status_code=404, detail=str(e)) from e
        except (ValueError, TypeError) as e:  # unsupported mode / bad request
            raise HTTPException(status_code=400, detail=str(e)) from e
        except ProviderError as e:  # includes design-phase NotYetImplemented
            raise HTTPException(status_code=501, detail=str(e)) from e

        return GenerateResponseModel(
            provider=result.provider,
            model_version=result.model_version,
            mode=result.mode,
            output_path=str(result.output_path),
            inference_seconds=result.inference_seconds,
            metrics=result.metrics,
        )

    return app


app = create_app()
