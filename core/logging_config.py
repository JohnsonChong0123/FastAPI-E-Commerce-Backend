# core/logging_config.py
import logging
from core.config import settings

class SensitiveDataFilter(logging.Filter):
    def filter(self, record):
        # Sanitize log messages by masking the eBay client secret if it appears in the log
        msg = str(record.msg)
        if settings.EBAY_CLIENT_SECRET and settings.EBAY_CLIENT_SECRET in msg:
            record.msg = msg.replace(settings.EBAY_CLIENT_SECRET, "******")
        return True

def setup_logging():
    logger = logging.getLogger("api_integration")
    logger.setLevel(logging.INFO)
    
    # 1. Create a handler (e.g., StreamHandler for console output)
    handler = logging.StreamHandler()
    
    # 2. Key: Add the filter to the handler or logger
    handler.addFilter(SensitiveDataFilter())
    
    # 3. Set the format
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    return logger

# Initialize the logger with the configured settings
logger = setup_logging()