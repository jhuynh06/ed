"""Shared Chroma client for all memory modules."""

from __future__ import annotations

import os

import chromadb

_chroma: chromadb.ClientAPI | None = None

CHROMA_DIR = os.environ.get("CHROMA_DIR", "./chroma_data")


def get_chroma() -> chromadb.ClientAPI:
    global _chroma
    if _chroma is None:
        _chroma = chromadb.PersistentClient(path=CHROMA_DIR)
    return _chroma
