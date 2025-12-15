from typing import Dict, Optional

from pydantic import BaseModel


class ValidationResult(BaseModel):
    is_valid: bool
    checks: Dict[str, bool]
    errors: Optional[Dict[str, str]] = None
