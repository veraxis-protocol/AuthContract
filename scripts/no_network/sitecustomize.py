"""Fail closed if Python code attempts an outbound socket connection."""

from __future__ import annotations

import socket


def _blocked(*_args: object, **_kwargs: object) -> None:
    raise RuntimeError("outbound network disabled by AuthContract verification guard")


socket.create_connection = _blocked  # type: ignore[assignment]
socket.socket.connect = _blocked  # type: ignore[assignment]
socket.socket.connect_ex = _blocked  # type: ignore[assignment]

