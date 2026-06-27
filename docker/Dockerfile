# syntax=docker/dockerfile:1.7
#
# Video AI Platform — GPU runtime image (RunPod RTX 4090 / L40S).
#
# Multi-stage so the heavy CUDA/PyTorch layer is cached independently of our
# fast-moving application code. The exact CUDA/PyTorch pins are finalized in
# Phase 1 against the SkyReels V3 / MultiTalk submodule requirements; the base
# tag below is the reviewed target (CUDA 12.x, proposal §11).

# ---- Base: CUDA 12.x runtime + Python 3.12 -------------------------------
ARG CUDA_IMAGE=nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04
FROM ${CUDA_IMAGE} AS base

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_SYSTEM_PYTHON=1 \
    HF_HOME=/workspace/.cache/huggingface

# Python 3.12 + git (for submodules) + ffmpeg (video I/O).
RUN apt-get update && apt-get install -y --no-install-recommends \
        software-properties-common ca-certificates curl git ffmpeg && \
    add-apt-repository ppa:deadsnakes/ppa && apt-get update && \
    apt-get install -y --no-install-recommends python3.12 python3.12-venv python3.12-dev && \
    rm -rf /var/lib/apt/lists/* && \
    ln -sf /usr/bin/python3.12 /usr/local/bin/python3 && \
    ln -sf /usr/bin/python3.12 /usr/local/bin/python

# uv for fast, reproducible installs (proposal §11).
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /workspace

# ---- Dependencies layer (cached unless pyproject changes) ----------------
FROM base AS deps
COPY pyproject.toml README.md ./
# Phase 1: add `--extra gpu` once torch/CUDA wheels are pinned here.
RUN uv pip install --system -e ".[dev]"

# ---- Application layer ----------------------------------------------------
FROM deps AS app
COPY . .
# Submodules are mounted/initialized at deploy time (weights are not baked in).
EXPOSE 8000

# Default: serve the REST API. Override CMD for CLI/benchmark runs.
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
