import logging
import os

logging.basicConfig(level=os.environ.get("SB_LOGLEVEL", "INFO"))
logger = logging.getLogger("stickybeak")
