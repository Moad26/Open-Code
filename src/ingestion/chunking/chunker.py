from typing import List
from uuid import uuid4

from src.ingestion.chunking.base_chunker import BaseChunker
from src.shared.models import Chapter, Chunk, ChunkMetadata, ParsedDoc


class MarkdownChunker(BaseChunker):
    def __init__(self, chunk_size: int, chunk_overlap: int) -> None:
        self.chunk_size = chunk_size * 4
        self.chunk_overlap = chunk_overlap * 4

    def _should_split(self, content: str) -> bool:
        return len(content) > self.chunk_size

    def _split_chapter(
        self, content: str, chapter: Chapter, source_title: str
    ) -> List[Chunk]:
        chunks: List[Chunk] = []
        start = 0
        content_length = len(content)

        while start < content_length:
            end = start + self.chunk_size
            chunk_text = content[start:end]
            char_start = chapter.char_span[0] + start
            char_end = chapter.char_span[1] + min(end, content_length)
            metadata = ChunkMetadata(
                source_doc_title=source_title,
                chapter_name=chapter.title,
                page_range=chapter.page_range,
                char_span=(char_start, char_end),
                chunk_id=uuid4(),
            )
            chunks.append(Chunk(content=chunk_text, metadata=metadata))
            start += self.chunk_size - self.chunk_overlap
        return chunks

    def chunk(self, doc: ParsedDoc) -> List[Chunk]:
        chunk_list: List[Chunk] = []
        text = doc.text
        chapters = doc.structure.chapters

        for chapter in chapters:
            content = text[chapter.char_span[0] : chapter.char_span[1]]

            if self._should_split(content):
                # Split large chapter into smaller chunks
                sub_chunks = self._split_chapter(content, chapter, doc.metadata.title)
                chunk_list.extend(sub_chunks)
            else:
                # Keep small chapter as single chunk
                metadata = ChunkMetadata(
                    source_doc_title=doc.metadata.title,
                    chapter_name=chapter.title,
                    page_range=chapter.page_range,
                    char_span=chapter.char_span,
                    chunk_id=uuid4(),
                )
                chunk_list.append(Chunk(content=content, metadata=metadata))

        return chunk_list
