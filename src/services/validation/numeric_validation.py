from src.models.models import InvoiceParseResult

from .interface import BaseValidator
from .validation_result import ValidationResult


class NumericValidator(BaseValidator):

    def validate(self, parsed: InvoiceParseResult) -> ValidationResult:
        pass
