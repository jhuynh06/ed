"""Shared Chroma client for all memory modules."""

from __future__ import annotations

import chromadb

_chroma: chromadb.ClientAPI | None = None


def get_chroma() -> chromadb.ClientAPI:
    global _chroma
    if _chroma is None:
        _chroma = chromadb.Client()
    return _chroma
