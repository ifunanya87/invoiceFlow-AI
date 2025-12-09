import datetime
import logging
import os
from pathlib import Path

# Project folders
ROOT_FOLDER = Path(__file__).resolve().parent.parent
LOG_FOLDER = os.path.join(ROOT_FOLDER, "logs")
os.makedirs(LOG_FOLDER, exist_ok=True)


# Timestamped log file
TIMESTAMP = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_file = os.path.join(LOG_FOLDER, f"invoiceflow_{TIMESTAMP}.log")


# Configure logging: console + file
handlers = [
    logging.StreamHandler(),
    logging.FileHandler(log_file, encoding="utf-8")
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
    handlers=handlers
)


# Central logger
logger = logging.getLogger("invoiceflow")
