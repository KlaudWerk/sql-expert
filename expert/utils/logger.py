from loguru import logger
import sys

def setup_logger():
    """Setup loguru logger with console and file outputs."""

    # Remove all existing handlers
    logger.remove()

    # Configure loguru logger
    config = {
        "handlers": [
            # Console handler with compact format
            {
                "sink": "sys.stdout",
                "format": "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
                "colorize": True,
            },
        ],
    }


    # Add our console handler
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        colorize=True
    )

    # Remove default handler and apply new configuration
    logger.configure(**config)
    return logger 

