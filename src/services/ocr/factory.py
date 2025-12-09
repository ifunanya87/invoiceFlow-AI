import logging
import os
import threading
from collections import OrderedDict
from typing import Any, Dict, Type

from .interface import BaseInvoiceExtractor
from .providers.paddleocr import PaddleOCRExtractor
from .providers.pdfplumber import PDFPlumberExtractor
from .providers.tesseract import TesseractExtractor

logger = logging.getLogger(__name__)


MAX_CACHE_SIZE = 4  # LRU capacity


# Extractor mapping
EXTRACTOR_MAPPING: Dict[str, Type[BaseInvoiceExtractor]] = {
    ".pdf": PDFPlumberExtractor,
    ".jpg": PaddleOCRExtractor,
    ".jpeg": PaddleOCRExtractor,
    ".png": PaddleOCRExtractor,
    ".tif": TesseractExtractor,
    ".tiff": TesseractExtractor,
    "default": TesseractExtractor,
}


# LRU cache (Thread-safe)
_CACHE_LOCK = threading.Lock()
_EXTRACTOR_INSTANCE_CACHE: "OrderedDict[Type[BaseInvoiceExtractor], BaseInvoiceExtractor]" = OrderedDict()


class InvoiceExtractorFactory:
    """
    Factory that returns the correct OCR extractor with:
    - Thread-safe lazy loading
    - LRU caching
    - Async wrapper
    """

    @staticmethod
    def get_extractor(source_path: str) -> BaseInvoiceExtractor:

        # Extract extension
        _, ext = os.path.splitext(source_path)
        ext = ext.lower()

        ExtractorClass = EXTRACTOR_MAPPING.get(ext, EXTRACTOR_MAPPING["default"])

        # Thread-safe LRU caching
        with _CACHE_LOCK:
            if ExtractorClass in _EXTRACTOR_INSTANCE_CACHE:
                # Update LRU
                _EXTRACTOR_INSTANCE_CACHE.move_to_end(ExtractorClass)
                logger.debug(f"[Factory] Cache HIT → {ExtractorClass.__name__}")
                return _EXTRACTOR_INSTANCE_CACHE[ExtractorClass]

            # Cache MISS → load instance
            logger.info(f"[Factory] Cache MISS → Loading {ExtractorClass.__name__}")

            instance = ExtractorClass()
            _EXTRACTOR_INSTANCE_CACHE[ExtractorClass] = instance
            _EXTRACTOR_INSTANCE_CACHE.move_to_end(ExtractorClass)

            # Enforce LRU capacity
            if len(_EXTRACTOR_INSTANCE_CACHE) > MAX_CACHE_SIZE:
                evicted_class, _ = _EXTRACTOR_INSTANCE_CACHE.popitem(last=False)
                logger.warning(f"[Factory] LRU Evicted → {evicted_class.__name__}")

            return instance


    # Async version
    @staticmethod
    async def aget_extractor(source_path: str) -> BaseInvoiceExtractor:
        """
        Async wrapper for FastAPI.
        """
        return InvoiceExtractorFactory.get_extractor(source_path)


    # OCR (sync)
    @staticmethod
    def extract(extractor: BaseInvoiceExtractor, source: Any) -> Any:
        return extractor.extract_data(source)


    # OCR (async)
    @staticmethod
    async def aextract(extractor: BaseInvoiceExtractor, source: Any) -> Any:
        return extractor.extract_data(source)


    # Reset cache
    @staticmethod
    def reset_cache():
        with _CACHE_LOCK:
            logger.info("[Factory] Cache reset")
            _EXTRACTOR_INSTANCE_CACHE.clear()
