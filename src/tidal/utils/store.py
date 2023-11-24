import gzip
from pathlib import Path
from typing import Any, Iterable, Iterator, Type, TypeVar

from tidal.utils.serialization import JSONSerializer

T = TypeVar("T")


def _open_func(path: Path, mode: str, encoding: str = "utf-8", **kwargs: Any):
    if path.suffix == ".gz":
        return gzip.open(path, mode+'t', encoding=encoding, **kwargs)
    else:
        return open(path, mode, encoding=encoding, **kwargs)


class JSONStore:
    @staticmethod
    def save(
        data: T,
        path: Path,
        mode: str = "w",
        encoding: str = "utf-8",
    ) -> None:
        data_str = JSONSerializer.serialize(data)
        with _open_func(path, mode, encoding=encoding) as fileobj:
            fileobj.write(data_str)

    @staticmethod
    def save_lines(
        stream: Iterable[T],
        path: Path,
        mode: str = "w",
        encoding: str = "utf-8",
    ) -> int:
        count = 0
        with _open_func(path, mode, encoding=encoding) as fileobj:
            for data in stream:
                fileobj.write(JSONSerializer.serialize(data))
                fileobj.write("\n")
                count += 1
            return count

    @staticmethod
    def load(path: Path, dtype: Type[T], encoding: str = "utf-8") -> T:
        with _open_func(path, "r", encoding=encoding) as fileobj:
            data = fileobj.read()
        return JSONSerializer.deserialize(data, dtype)

    @staticmethod
    def load_lines(path: Path, dtype: Type[T], encoding: str = "utf-8") \
            -> Iterator[T]:
        with _open_func(path, "r", encoding=encoding) as fileobj:
            for line in fileobj:
                data = line.rstrip("\n")
                yield JSONSerializer.deserialize(data, dtype)
