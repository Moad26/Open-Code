from typing import List

from src.ingestion.chunking.base_chunker import BaseChunker
from src.shared.models import Chunk, ParsedDoc


class MarkdownChunker(BaseChunker):
    def __init__(self, chunk_size, chunk_overlap) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(doc: ParsedDoc) -> List[Chunk]:
        pass
