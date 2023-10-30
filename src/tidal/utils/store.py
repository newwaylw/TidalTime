from pathlib import Path
from typing import Iterable, Iterator, Type, TypeVar

from tidal.utils.file_utils import AutoFileOpener, openTextMode
from tidal.utils.serialization import JSONSerializer

T = TypeVar("T")


class JSONStore:
    def __init__(self):
        self.file_opener = AutoFileOpener()

    def save(
        self,
        data: T,
        path: Path,
        mode: openTextMode = "w",
        encoding: str = "utf-8",
    ) -> None:
        data_str = JSONSerializer.serialize(data)
        with self.file_opener.open(path, mode, encoding=encoding) as fileobj:
            fileobj.write(data_str)

    def save_lines(
        self,
        stream: Iterable[T],
        path: Path,
        mode: openTextMode = "w",
        encoding: str = "utf-8",
    ) -> int:
        count = 0
        with self.file_opener.open(path, mode, encoding=encoding) as fileobj:
            for data in stream:
                fileobj.write(JSONSerializer.serialize(data))
                fileobj.write("\n")
                count += 1
            return count

    def load(self, path: Path, dtype: Type[T], encoding: str = "utf-8") -> T:
        with self.file_opener.open(path, "r", encoding=encoding) as fileobj:
            data = fileobj.read()
        return JSONSerializer.deserialize(data, dtype)

    def load_lines(
        self, path: Path, dtype: Type[T], encoding: str = "utf-8"
    ) -> Iterator[T]:
        """Stream a file with json objects of dtype on each line"""
        with self.file_opener.open(path, "r", encoding=encoding) as fileobj:
            for line in fileobj:
                data = line.rstrip("\n")
                yield JSONSerializer.deserialize(data, dtype)
