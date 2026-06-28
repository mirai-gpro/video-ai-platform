"""Model-agnostic orchestration layer.

The Pipeline is the single place that turns a high-level request into a
Provider call. It resolves the Provider by name through the registry,
validates the requested mode against the Provider's declared capabilities,
dispatches to the right method, and (when a recorder is wired) measures and
records the benchmark. It must NEVER import or branch on a specific model.
"""

from pipeline.pipeline import Pipeline, PipelineRequest, build_pipeline

__all__ = ["Pipeline", "PipelineRequest", "build_pipeline"]
