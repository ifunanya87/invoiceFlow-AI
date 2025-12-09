from typing import Dict, Type

from .interface import BaseParser
from .providers.heuristic_parser import HeuristicParser

# from .providers.llm_parser import LLMParser


PARSER_MAPPING: Dict[str, Type[BaseParser]] = {
    "heuristic": HeuristicParser,
    # "llm": LLMParser,
}

class ParserFactory:
    """
    Factory that returns a parser instance based on a given parser name.
    """

    @staticmethod
    def get_parser(parser_name: str) -> BaseParser:
        parser_name = parser_name.lower()

        if parser_name not in PARSER_MAPPING:
            raise ValueError(f"Unknown parser '{parser_name}'. Available: {list(PARSER_MAPPING.keys())}")

        ParserClass = PARSER_MAPPING[parser_name]
        return ParserClass()
