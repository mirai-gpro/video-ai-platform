"""Provider registry — resolves a provider name to a ``VideoProvider``.

The shared layers (Pipeline, API, CLI) ask the registry for a Provider by
name; they never import a concrete Provider class directly. This keeps model
selection a runtime config concern and makes "add a model = register a
Provider" literally true.

Registration is explicit (no import-time magic scanning) so the dependency
graph stays readable and a missing GPU dependency in one Provider can't break
the whole process at import time.
"""

from __future__ import annotations

from collections.abc import Callable

from providers.base import VideoProvider

ProviderFactory = Callable[[], VideoProvider]

_REGISTRY: dict[str, ProviderFactory] = {}


def register(name: str, factory: ProviderFactory) -> None:
    """Register a Provider factory under ``name`` (idempotent per name)."""
    key = name.lower()
    if key in _REGISTRY:
        raise ValueError(f"Provider '{name}' is already registered")
    _REGISTRY[key] = factory


def available() -> list[str]:
    """Names of all registered Providers."""
    return sorted(_REGISTRY)


def create(name: str) -> VideoProvider:
    """Instantiate the Provider registered under ``name``.

    Factories are lazy: the (heavy) model object is only built when a Provider
    is actually requested, so importing the registry never loads CUDA.
    """
    key = name.lower()
    try:
        factory = _REGISTRY[key]
    except KeyError:
        raise KeyError(
            f"Unknown provider '{name}'. Available: {available() or '(none registered)'}"
        ) from None
    return factory()


def _bootstrap() -> None:
    """Register the built-in Providers.

    Imports are local so a failure to import one Provider's (GPU) dependencies
    does not prevent the others from registering.

    Active scope: OmniAvatar 1.3B only. Other models (e.g. MultiTalk for
    multi-person dialogue) are deferred (ADR-0004); when added they are one
    more registration — nothing upstream of the Provider boundary changes.
    """
    try:
        from providers.omniavatar import register_provider as _omniavatar

        _omniavatar()
    except Exception:  # noqa: BLE001 - design-phase tolerance; logged in Phase 1
        pass


_bootstrap()
