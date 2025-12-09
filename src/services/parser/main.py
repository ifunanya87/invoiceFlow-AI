import argparse
import datetime
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

from src.services.logging_config import logger
from src.services.ocr.main import process_invoice

from .factory import ParserFactory

# Project folders and timestamp
ROOT_FOLDER = Path(__file__).resolve().parent.parent.parent
RESULT_FOLDER = os.path.join(ROOT_FOLDER, "output")
os.makedirs(RESULT_FOLDER, exist_ok=True)

TIMESTAMP = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# Valid invoice file extensions
VALID_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff"}


# Single file parser
def run_parser(file_path: str, parser_name: str = "heuristic") -> Dict[str, Any]:
    logger.info(f"Processing file: {file_path} with parser: {parser_name}")

    ocr_output = process_invoice(file_path)

    if "error" in ocr_output:
        logger.warning(f"OCR error for {file_path}: {ocr_output['error']}")
        return {"error": ocr_output["error"]}

    raw_text = ocr_output.get("raw_text")
    if not raw_text:
        logger.warning(f"OCR returned no text for {file_path}")
        return {"error": "OCR returned no text."}

    parser = ParserFactory.get_parser(parser_name)
    structured = parser.parse(raw_text)

    logger.info(f"Parsed {file_path}: {len(raw_text)} characters extracted")

    return {
        "raw_data": raw_text,
        "structured_data": structured
    }


# Batch parser
def run_batch(path: str, parser_name: str = "heuristic", as_json: bool = True):
    logger.info(f"Starting batch processing for path: {path}")

    file_paths: List[str] = []

    # Folder mode
    if os.path.isdir(path):
        for f in os.listdir(path):
            full_path = os.path.join(path, f)
            ext = os.path.splitext(f)[1].lower()
            if os.path.isfile(full_path) and ext in VALID_EXTENSIONS:
                file_paths.append(full_path)
        logger.info(f"Found {len(file_paths)} invoice files in folder")

    # File mode
    elif os.path.isfile(path):
        file_paths = [path]

    # Invalid path
    else:
        error = {"error": f"Path does not exist: {path}"}
        logger.error(error["error"])
        return json.dumps(error, indent=4) if as_json else error

    results = []
    for fp in file_paths:
        parsed = run_parser(fp, parser_name)
        results.append({
            "file": os.path.basename(fp),
            "full_path": fp,
            "parser_used": parser_name,
            "result": parsed
        })

    # Save batch results to timestamped JSON
    output_file = os.path.join(RESULT_FOLDER, f"results_{TIMESTAMP}.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
    logger.info(f"Saved batch results to {output_file}")

    return json.dumps(results, indent=4) if as_json else results


# CLI
def cli():
    parser = argparse.ArgumentParser(description="Run invoice parser (single or batch mode).")
    parser.add_argument("path", help="Path to an invoice file or a folder of invoices.")
    parser.add_argument(
        "parser_name",
        nargs="?",
        default="heuristic",
        help="Parser to use: heuristic | llm"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Return output as formatted JSON"
    )

    args = parser.parse_args()
    result = run_batch(args.path, args.parser_name, as_json=args.json)
    print(result)


# Entry point
if __name__ == "__main__":
    cli()
