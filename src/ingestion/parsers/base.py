import os
from abc import ABC, abstractmethod

from src.shared.models import ParsedDoc


class BaseParser(ABC):
    @abstractmethod
    def parse(self, pdf_path: os.PathLike) -> ParsedDoc:
        pass
