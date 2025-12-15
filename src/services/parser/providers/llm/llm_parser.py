import logging
from typing import Optional

import pandas as pd

from src.config import get_settings
from src.models.models import InvoiceParseResult, OCRResult
from src.services.parser.interface import BaseParser
from src.services.parser.parser_registry import register_parser

from .retry_llm_utils import call_llm_with_retry

logger = logging.getLogger(__name__)
settings = get_settings()

# Conditional registration
if settings.llm and settings.llm.openai_api_key:
    @register_parser("llm", requires_api_key=True)
    class LLMParser(BaseParser):
        """
        OCR-output–aware LLM parser.
        Handles:
        - Raw text OCR
        - Table OCR (DataFrame)
        Returns a single InvoiceParseResult.
        """

        def __init__(self, model_name: str = "gpt-4o-mini"):

            self.settings = get_settings()
            self.model_name = self.settings.llm.model_name
            self.max_retries = self.settings.llm.max_retries
            self.retry_delay = self.settings.llm.retry_delay_sec

            # Lazy imports
            from langchain_core.output_parsers import JsonOutputParser
            from langchain_core.prompts import PromptTemplate
            from langchain_openai import ChatOpenAI

            # Validate api -key
            if not self.settings.llm.openai_api_key:
                raise ValueError(
                    "OPENAI_API_KEY not set. "
                    "This is required when using the LLM parser."
                )

            try:
                self.llm = ChatOpenAI(
                    model=self.model_name,
                    openai_api_key=self.settings.llm.openai_api_key,
                    temperature=0,
                )

                # Output parser
                self.output_parser = JsonOutputParser(
                    pydantic_object=InvoiceParseResult
                )

                self.text_prompt = PromptTemplate(
                    template=(
                        "Extract structured invoice information from OCR text.\n"
                        "{format_instructions}\n"
                        "OCR TEXT:\n{context}\n"
                    ),
                    input_variables=["context"],
                    partial_variables={
                        "format_instructions": self.output_parser.get_format_instructions()
                    },
                )

                self.table_prompt = PromptTemplate(
                    template=(
                        "Extract structured invoice information from OCR table output.\n"
                        "Each line contains bounding box coordinates and detected text.\n"
                        "Use spatial grouping to reconstruct invoice structure.\n\n"
                        "{format_instructions}\n"
                        "OCR TABLE DATA:\n{context}\n"
                    ),
                    input_variables=["context"],
                    partial_variables={
                        "format_instructions": self.output_parser.get_format_instructions()
                    },
                )

                logger.info(f"[LLMParser] Initialized with model={self.model_name}")

            except Exception as e:
                logger.exception("Failed to initialize LLMParser")
                raise e


        def parse(self, ocr_output: OCRResult) -> InvoiceParseResult:
            """
            Main entrypoint. Accepts OCR output (text or DataFrame).
            """

            ocr_type = self._detect_ocr_type(ocr_output)

            if ocr_type == "table":
                context = self._serialize_table(ocr_output.tables)
                prompt = self.table_prompt
            else:
                context = ocr_output.text.strip()
                prompt = self.text_prompt

            if not context:
                return InvoiceParseResult(
                    error="No OCR content provided",
                    raw_text_length=0
                )

            chain = prompt | self.llm | self.output_parser

            result: InvoiceParseResult = call_llm_with_retry(
                chain,
                context=context,
                retries=self.max_retries
            )

            result.raw_text_length = len(context)
            return result

        # Helpers
        def _detect_ocr_type(self, ocr_result: OCRResult) -> str:
            """
            Detect whether the OCRResult contains a table or text.
            """

            if ocr_result.tables is not None:
                return "table"
            return "text"


        def _serialize_table(self, df: pd.DataFrame) -> str:
            """
            Converts OCR table DataFrame into LLM-readable text.
            """
            lines = []
            for _, row in df.iterrows():
                lines.append(
                    f"[{row.x_min},{row.y_min} → {row.x_max},{row.y_max}] {row.text}"
                )
            return "\n".join(lines)


# LLM parser unavailable
else:
    PARSER_REGISTRY["llm"] = ParserMeta(
        cls=None,
        requires_api_key=True,
        available=False,
        reason="OPENAI_API_KEY not set"
    )
    logger.info("[LLMParser] LLM parser not registered: OPENAI_API_KEY not set")
