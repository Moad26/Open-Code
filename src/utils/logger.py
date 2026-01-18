import sys
from functools import lru_cache

from loguru import logger


@lru_cache()
def setup_logger():
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO",
    )

    logger.add(
        "logs/app.log",
        rotation="500 MB",
        retention="10 days",
        level="DEBUG",
    )

    logger.add(
        "logs/app.json",
        rotation="500 MB",
        retention="10 days",
        level="DEBUG",
        serialize=True,
    )
    pass
