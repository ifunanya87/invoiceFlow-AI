from abc import ABC, abstractmethod
from typing import Any


class BaseInvoiceExtractor(ABC):
    """ Abstract OCR interface """

    @abstractmethod
    def extract_data(self, source: Any) -> str:
        pass
