from dataclasses import dataclass
from typing import Dict, Type

from .interface import BaseParser


@dataclass(frozen=True)
class ParserMeta:
    cls: Type[BaseParser]
    requires_api_key: bool = False


PARSER_REGISTRY: Dict[str, ParserMeta] = {}


def register_parser(
    name: str,
    *,
    requires_api_key: bool = False
):
    def wrapper(cls: Type[BaseParser]):
        PARSER_REGISTRY[name.lower()] = ParserMeta(
            cls=cls,
            requires_api_key=requires_api_key
        )
        return cls
    return wrapper
