from abc import ABC, abstractmethod
from typing import Any, Dict

InvoiceData = Dict[str, Any]

class BaseParser(ABC):
    """
    Abstract base class for all invoice parsers.
    """

    @abstractmethod
    def parse(self, raw_text: str) -> InvoiceData:
        """Convert raw OCR text into structured invoice fields."""
        pass
