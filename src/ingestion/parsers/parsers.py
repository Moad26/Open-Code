import os

from shared.models import ParsedDoc

from .base import BaseParser


class DoclingParser(BaseParser):
    def parse(self, pdf_path: os.PathLike) -> ParsedDoc:
        pass
