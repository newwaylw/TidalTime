import gzip
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional, TextIO

from typing_extensions import Literal, TypeAlias

openTextMode: TypeAlias = Literal["r", "a", "w", "x"]
gzipOpenTextMode: TypeAlias = Literal["rt", "at", "wt", "xt"]


class BaseFileOpener(ABC):
    @abstractmethod
    def open(
        self,
        path: Path,
        mode: openTextMode = "r",
        encoding: str = "utf-8",
        **kwargs: Any,
    ) -> TextIO:
        pass


class RegularFileOpener(BaseFileOpener):
    def open(
        self,
        path: Path,
        mode: openTextMode = "r",
        encoding: str = "utf-8",
        **kwargs: Any,
    ) -> TextIO:
        return open(path, mode, encoding=encoding, **kwargs)


class GzipFileOpener(BaseFileOpener):
    def open(
        self,
        path: Path,
        mode: openTextMode = "r",
        encoding: str = "utf-8",
        **kwargs: Any,
    ) -> TextIO:
        gzip_mode: Optional[gzipOpenTextMode] = None
        if mode == "r":
            gzip_mode = "rt"
        if mode == "w":
            gzip_mode = "wt"
        if mode == "x":
            gzip_mode = "xt"
        if mode == "a":
            gzip_mode = "at"
        assert gzip_mode is not None

        return gzip.open(path, gzip_mode, encoding=encoding, **kwargs)


class AutoFileOpener(BaseFileOpener):
    def open(
        self,
        path: Path,
        mode: openTextMode = "r",
        encoding: str = "utf-8",
        **kwargs: Any,
    ) -> TextIO:
        if path.suffix == ".gz":
            return GzipFileOpener().open(
                path, mode, encoding=encoding, **kwargs
            )
        return RegularFileOpener().open(
            path, mode, encoding=encoding, **kwargs
        )
