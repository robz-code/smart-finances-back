from typing import Generic, List, TypeVar

from pydantic import BaseModel
from pydantic.generics import GenericModel

T = TypeVar("T")


class MessageResponse(BaseModel):
    message: str

    def __init__(self, message: str):
        super().__init__(message=message)


class SearchResponse(GenericModel, Generic[T]):
    total: int
    results: List[T]

    model_config = {"arbitrary_types_allowed": True}
