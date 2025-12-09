from typing import Any

import cv2
import numpy as np
from paddleocr import PaddleOCR
from PIL import Image

from ..interface import BaseInvoiceExtractor


class PaddleOCRExtractor(BaseInvoiceExtractor):
    """Extractor for image invoices using PaddleOCR (robust to layout variations)."""

    def __init__(self, lang='en'):
        self.ocr_model = PaddleOCR(use_textline_orientation=True, lang=lang)

    def extract_data(self, source: Any) -> str:
        """
        Performs OCR on the image source and returns the extracted text.
        """
        img_array = None

        try:
            # Handle PIL Images
            if isinstance(source, Image.Image):
                if source.mode != "RGB":
                    source = source.convert("RGB")
                img_array = np.array(source)


            # Handle file paths
            elif isinstance(source, str):
                img_array = cv2.imread(source)
                if img_array is None:
                    raise FileNotFoundError(f"OpenCV failed to load image from path: {source}")

                # Convert to RGB
                if len(img_array.shape) == 2:
                    img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)
                elif img_array.shape[2] == 4:
                    img_array = cv2.cvtColor(img_array, cv2.COLOR_BGRA2RGB)
                elif img_array.shape[2] == 3:
                    img_array = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB)
                else:
                    raise ValueError(f"Unsupported number of channels: {img_array.shape}")

            else:
                raise TypeError("Source must be a file path (str) or a PIL Image object.")


            # Reduce noise
            img_array = cv2.medianBlur(img_array, 5)


            # Resize large images
            MAX_SIZE = 960
            h, w = img_array.shape[:2]
            if max(h, w) > MAX_SIZE:
                scale = MAX_SIZE / max(h, w)
                img_array = cv2.resize(img_array, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)


            # Run OCR
            result = self.ocr_model.predict(img_array)

        except Exception as e:
            print(f"Error during PaddleOCR execution: {e}")
            return {"error": f"PaddleOCR failed: {str(e)}",
                    "total_amount": None,
                    "invoice_id": None,
                    "invoice_date": None,
                    "vendor_name": None,
                    "raw_text_length": 0}


        # Safely parse OCR results
        raw_text = "\n".join(result[0]['rec_texts'])

        return raw_text


# CLI for testing
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python file.py <image_path>")
        exit(1)

    img_path = sys.argv[-1]

    extractor = PaddleOCRExtractor()
    result = extractor.extract_data(img_path)
    print(result)
    print("-" * 30)
    print(type(result))
