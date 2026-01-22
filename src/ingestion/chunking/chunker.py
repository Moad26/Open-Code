from typing import List
from uuid import uuid4

from src.ingestion.chunking.base_chunker import BaseChunker
from src.shared.models import Chunk, ParsedDoc


class MarkdownChunker(BaseChunker):
    def __init__(self, chunk_size, chunk_overlap) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, doc: ParsedDoc) -> List[Chunk]:
        chunk_list: List[Chunk] = []
        text = doc.text
        chapters = doc.structure.chapters
        for chapter in chapters:
            data = {}
            data["content"] = text[chapter.char_span[0] : chapter.char_span[1]]
            data["source_doc_title"] = doc.metadata.title
            data["chapter_name"] = chapter.title
            data["page_range"] = chapter.page_range
            data["char_span"] = chapter.char_span
            data["chunk_id"] = uuid4()
            chunk_list.append(Chunk(**data))
        return chunk_list
