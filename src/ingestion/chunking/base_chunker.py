from abc import ABC, abstractmethod
from typing import List

from src.shared.models import Chunk, ParsedDoc


class BaseChunker(ABC):
    @abstractmethod
    def chunk(self, doc: ParsedDoc) -> List[Chunk]:
        pass
