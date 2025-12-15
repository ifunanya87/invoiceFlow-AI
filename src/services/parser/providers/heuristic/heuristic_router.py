from src.models.models import OCRResult
from src.services.parser.interface import BaseParser
from src.services.parser.parser_registry import register_parser

from .heuristic_table import HeuristicTableParser
from .heuristic_text import HeuristicTextParser


@register_parser("heuristic")
class HeuristicRouterParser(BaseParser):

    def __init__(self):
        self.text_parser = HeuristicTextParser()
        self.table_parser = HeuristicTableParser()

    def parse(self, ocr_result: OCRResult):
        if ocr_result.tables is not None:
            return self.table_parser.parse(ocr_result.tables)

        return self.text_parser.parse(ocr_result.text)
