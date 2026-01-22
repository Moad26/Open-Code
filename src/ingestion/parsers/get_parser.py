from src.ingestion.parsers.base import BaseParser
from src.ingestion.parsers.parsers import DoclingParser, MarkerParser
from src.utils.config import settings


def get_parser() -> BaseParser:
    name = settings.parsing.parser
    if name == "docling":
        return DoclingParser()
    elif name == "marker":
        return MarkerParser()
    raise ValueError(f"Unknown parser: {name}")
