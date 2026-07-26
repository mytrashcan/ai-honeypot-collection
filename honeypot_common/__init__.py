"""Shared primitives used by the independently deployable honeypots."""

from .events import EventRecorder, install_fastapi_tracking, mark_signal

__all__ = ["EventRecorder", "install_fastapi_tracking", "mark_signal"]
