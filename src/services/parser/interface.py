from abc import ABC, abstractmethod

from src.models.models import InvoiceParseResult


class BaseParser(ABC):
    """
    Abstract base class for all invoice parsers.
    """

    @abstractmethod
    def parse(self, raw_text: str) -> InvoiceParseResult:
        """Convert raw OCR text into structured invoice fields."""
        pass
