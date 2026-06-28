"""Command-line interface (``vap``).

Thin Typer wrapper over the same Pipeline the REST API uses, proving the
common-interface claim: CLI and API are two front-ends over one orchestration
layer with zero model-specific code.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer

from pipeline import PipelineRequest, build_pipeline
from providers import available, create
from providers.base import (
    GenerationMode,
    GenerationRequest,
    ProviderError,
    TalkingAvatarRequest,
    VideoSpec,
)

app = typer.Typer(help="Video AI Platform CLI", no_args_is_help=True)


@app.command("providers")
def list_providers() -> None:
    """List registered providers and their supported modes."""
    for name in available():
        info = create(name).info
        modes = ", ".join(sorted(m.value for m in info.modes))
        typer.echo(f"{info.name} ({info.model_version}): {modes}")


@app.command()
def generate(
    provider: str = typer.Option(..., help="Provider name, e.g. skyreels"),
    prompt: str = typer.Option("", help="Text prompt"),
    output: Path = typer.Option(Path("outputs/out.mp4"), help="Output file"),
    width: int = 1280,
    height: int = 720,
    fps: int = 24,
    duration: float = 15.0,
) -> None:
    """Run text-to-video generation."""
    req = PipelineRequest(
        provider=provider,
        mode=GenerationMode.TEXT_TO_VIDEO,
        mode_request=GenerationRequest(
            prompt=prompt,
            output_path=output,
            spec=VideoSpec(width=width, height=height, fps=fps, duration_seconds=duration),
        ),
    )
    _run(req)


@app.command("talking-avatar")
def talking_avatar(
    provider: str = typer.Option(...),
    image: Path = typer.Option(..., help="Reference image"),
    audio: Path = typer.Option(..., help="Driving audio"),
    output: Path = typer.Option(Path("outputs/out.mp4")),
) -> None:
    """Run talking-avatar generation."""
    req = PipelineRequest(
        provider=provider,
        mode=GenerationMode.TALKING_AVATAR,
        mode_request=TalkingAvatarRequest(
            reference_image=image, audio=audio, output_path=output
        ),
    )
    _run(req)


def _run(req: PipelineRequest) -> None:
    try:
        result = build_pipeline().run(req)
    except (KeyError, ValueError, TypeError) as e:
        raise typer.BadParameter(str(e)) from e
    except ProviderError as e:
        typer.secho(f"Not available yet: {e}", fg=typer.colors.YELLOW)
        raise typer.Exit(code=2) from e
    typer.echo(
        json.dumps(
            {
                "provider": result.provider,
                "output": str(result.output_path),
                "inference_seconds": result.inference_seconds,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    app()
