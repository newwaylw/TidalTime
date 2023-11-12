import abc
from typing import Type, TypeVar

from serde.json import from_json, to_json

T = TypeVar("T")


class JSONSerializer:
    @classmethod
    def serialize(
        cls,
        data: T,
    ) -> str:
        return to_json(data)

    @classmethod
    def deserialize(cls, data: str, dtype: Type[T]) -> T:
        return from_json(dtype, data)
