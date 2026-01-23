"""Unit tests for MarkdownChunker."""

import pytest
from uuid import UUID
from src.ingestion.chunking.chunker import MarkdownChunker
from src.shared.models import Chapter, Chunk


class TestMarkdownChunkerUnit:
    @pytest.mark.parametrize(
        "chunk_size, chunk_overlap, content_len, expected",
        [
            (
                10,
                2,
                40,
                False,
            ),  # 40 == 10*4, exact size, should not split? Logic says > chunk_size
            (10, 2, 41, True),  # 41 > 40, should split
            (10, 2, 39, False),  # 39 < 40, should not split
        ],
    )
    def test_should_split(self, chunk_size, chunk_overlap, content_len, expected):
        """Test _should_split logic with internal multiplication (x4)."""
        chunker = MarkdownChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        # Internal chunk_size will be chunk_size * 4
        # expected is based on length > internal_chunk_size

        content = "a" * content_len
        assert chunker._should_split(content) == expected

    def test_split_chapter_sliding_window(self):
        """Test the sliding window logic of _split_chapter."""
        # Input params
        chunk_size = 10
        chunk_overlap = 2
        # Internal: size=40, overlap=8
        chunker = MarkdownChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        # Create content length 100
        # Expected behavior:
        # 1. 0-40
        # 2. (40-8)=32 -> 32+40=72
        # 3. (72-8)=64 -> 64+40=104 (capped at 100)
        # So 3 chunks expected.
        content = "x" * 100
        chapter = Chapter(
            number=1,
            title="Test Chapter",
            page_range=(1, 5),
            char_span=(1000, 1100),  # Offset in doc
        )

        chunks = chunker._split_chapter(content, chapter, "Source Title")

        assert len(chunks) == 3

        # Verify Chunk 1
        assert len(chunks[0].content) == 40
        assert chunks[0].metadata.char_span == (1000, 1040)

        # Verify Chunk 2
        # Start at 32 relative to content, so absolute 1032
        assert len(chunks[1].content) == 40
        assert chunks[1].metadata.char_span == (1032, 1072)

        # Verify Chunk 3
        # Start at 64 relative to content, so absolute 1064
        # End at 100 relative, so absolute 1100
        assert len(chunks[2].content) == 36  # 100 - 64
        assert chunks[2].metadata.char_span == (1064, 1100)

        # Verify Overlap
        # Chunk 1 end=40, Chunk 2 start=32. Overlap = 8. Correct.

    def test_split_chapter_metadata_mapping(self):
        """Verify char_span correctly maps back to original doc coordinates."""
        chunker = MarkdownChunker(chunk_size=10, chunk_overlap=2)
        content = "a" * 50
        chapter_start = 500
        chapter = Chapter(
            number=1,
            title="Map Test",
            page_range=(1, 1),
            char_span=(chapter_start, chapter_start + 50),
        )

        chunks = chunker._split_chapter(content, chapter, "Doc 1")

        # Internal size 40, overlap 8.
        # Chunks: 0-40, 32-50.

        c1 = chunks[0]
        c2 = chunks[1]

        assert c1.metadata.char_span == (500, 540)
        assert c2.metadata.char_span == (532, 550)
        assert c1.metadata.chapter_name == "Map Test"
        assert c1.metadata.source_doc_title == "Doc 1"

    def test_edge_cases(self):
        """Test edge cases: small chapter, empty chapter."""
        chunker = MarkdownChunker(chunk_size=10, chunk_overlap=2)
        # Internal size 40.

        # 1. Exact size
        content_exact = "a" * 40
        chapter = Chapter(number=1, title="Exact", page_range=(1, 1), char_span=(0, 40))
        chunks = chunker._split_chapter(content_exact, chapter, "T")
        assert len(chunks) == 1
        assert chunks[0].content == content_exact

        # 2. Smaller than size (should yield 1 chunk if called directly, though usually filtered by _should_split)
        content_small = "a" * 10
        chunks = chunker._split_chapter(content_small, chapter, "T")
        assert len(chunks) == 1
        assert chunks[0].content == content_small

        # 3. Valid UUIDs
        assert isinstance(chunks[0].metadata.chunk_id, UUID)
