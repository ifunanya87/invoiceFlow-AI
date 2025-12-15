from src.config import get_settings

from .parser_registry import PARSER_REGISTRY


class ParserFactory:
    @staticmethod
    def get_parser(parser_name: str):
        parser_name = parser_name.lower()

        if parser_name not in PARSER_REGISTRY:
            raise ValueError(
                f"Unknown parser '{parser_name}'. "
                f"Available: {list(PARSER_REGISTRY.keys())}"
            )

        meta = PARSER_REGISTRY[parser_name]
        settings = get_settings()

        if meta.requires_api_key and not settings.llm.openai_api_key:
            raise RuntimeError(
                f"Parser '{parser_name}' requires OPENAI_API_KEY"
            )

        return meta.cls()
