"""
Storage abstraction layer for the Electronic Lab Notebook.

LocalStorage is the default implementation backed by the local filesystem.
The interface mirrors what an S3Storage implementation would need, so swapping
backends is a one-line change in attachment_service.py.
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod


class StorageBackend(ABC):
    """Abstract storage interface. Implement this to add S3 or GCS support."""

    @abstractmethod
    def save(self, path: str, data: bytes) -> str:
        """
        Persist *data* at the given *path* (relative to the backend root).
        Returns the canonical stored path.
        """
        ...

    @abstractmethod
    def load(self, path: str) -> bytes:
        """Load and return the raw bytes stored at *path*."""
        ...

    @abstractmethod
    def delete(self, path: str) -> None:
        """Remove the file at *path*. No-op if the file does not exist."""
        ...

    @abstractmethod
    def exists(self, path: str) -> bool:
        """Return True if a file exists at *path*."""
        ...


class LocalStorage(StorageBackend):
    """
    Filesystem-backed storage.

    All paths are relative to *base_dir* (default: settings.UPLOAD_DIR).
    The S3Storage replacement would accept a bucket name instead.
    """

    def __init__(self, base_dir: str | None = None) -> None:
        from app.config import settings

        self.base_dir = base_dir or settings.UPLOAD_DIR

    def _full_path(self, path: str) -> str:
        # Strip any leading slash so os.path.join works correctly
        return os.path.join(self.base_dir, path.lstrip("/"))

    def save(self, path: str, data: bytes) -> str:
        full = self._full_path(path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as fh:
            fh.write(data)
        return path

    def load(self, path: str) -> bytes:
        full = self._full_path(path)
        with open(full, "rb") as fh:
            return fh.read()

    def delete(self, path: str) -> None:
        full = self._full_path(path)
        try:
            os.remove(full)
        except FileNotFoundError:
            pass

    def exists(self, path: str) -> bool:
        return os.path.isfile(self._full_path(path))


# Module-level singleton — replace with S3Storage() for cloud deployments
storage: StorageBackend = LocalStorage()
