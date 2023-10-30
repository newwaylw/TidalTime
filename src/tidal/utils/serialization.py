import abc
from typing import Type, TypeVar

from serde.json import from_json, to_json

T = TypeVar("T")


class AbstractSerializer(abc.ABC):
    @abc.abstractmethod
    def serialize(self, data: T) -> str:
        pass

    @abc.abstractmethod
    def deserialize(self, data: str, dtype: Type[T]) -> T:
        pass


class JSONSerializer(AbstractSerializer):
    def __init__(self):
        pass

    def serialize(
        self,
        data: T,
    ) -> str:
        return to_json(data)

    def deserialize(self, data: str, dtype: Type[T]) -> T:
        return from_json(dtype, data)
