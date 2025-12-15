from abc import ABC, abstractmethod

from src.models.models import InvoiceParseResult


class BaseValidator(ABC):

    @abstractmethod
    def validate(self, parsed: InvoiceParseResult):
        pass
