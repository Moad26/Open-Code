import sys
from functools import lru_cache

from loguru import logger

from src.utils.config import settings


@lru_cache()
def setup_logger():
    logging_dir = settings.logging.log_dir
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="WARNING",
    )

    logger.add(
        logging_dir / "app.log",
        rotation="500 MB",
        retention="10 days",
        level="DEBUG",
    )

    logger.add(
        logging_dir / "app.json",
        rotation="500 MB",
        retention="10 days",
        level="DEBUG",
        serialize=True,
    )
    return logger


logger = setup_logger()
