import json
import re
from typing import Any, Optional

from pydantic import ValidationError

from src.models.models import InvoiceParseResult


def extract_json(text: str) -> Optional[str]:
    """
    Extract a JSON object from any LLM output.
    - Removes backticks
    - Finds the first {...} block
    """
    if not text:
        return None

    # Remove code fence
    text = text.replace("```json", "").replace("```", "").strip()

    # Extract the first {...} using a greedy balanced match
    match = re.search(r"\{.*\}", text, re.DOTALL)
    return match.group(0) if match else None


def call_llm_with_retry(chain: Any, retries: int = 3, **inputs) -> InvoiceParseResult:
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            # Invoke LLM
            response = chain.invoke({"context": raw_text})

            if isinstance(response, InvoiceParseResult):
                return response

            # Convert possible object → text → json
            if hasattr(response, "json"):
                text = response.json()
            else:
                text = str(response)

            # Extract JSON from messy LLM text
            cleaned_json = extract_json(text)
            if cleaned_json is None:
                raise ValueError(f"No JSON found in response (attempt {attempt})")

            # Validate with Pydantic
            parsed = InvoiceParseResult.parse_raw(cleaned_json)
            return parsed

        except (json.JSONDecodeError, ValidationError, ValueError) as e:
            last_error = e
            continue  # retry

    # After all retries fail → return structured error
    return InvoiceParseResult(
        error=f"LLM JSON parsing failed after {retries} attempts: {last_error}",
        raw_text_length=len(raw_text)
    )
