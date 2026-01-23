"""Integration tests for MarkdownChunker."""

import pytest
from uuid import UUID
from src.ingestion.chunking.chunker import MarkdownChunker
from src.shared.models import Chunk, ParsedDoc


class TestMarkdownChunkerIntegration:
    @pytest.mark.parametrize(
        "chunk_size, chunk_overlap",
        [
            (10, 2),  # Internal: 40, 8
            (20, 5),  # Internal: 80, 20
        ],
    )
    def test_end_to_end_flow(
        self, sample_parsed_doc: ParsedDoc, chunk_size, chunk_overlap
    ):
        """Test processing a full ParsedDoc."""
        chunker = MarkdownChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        chunks = chunker.chunk(sample_parsed_doc)

        assert isinstance(chunks, list)
        assert len(chunks) > 0
        assert all(isinstance(c, Chunk) for c in chunks)

        # Verify content coverage
        # sample_parsed_doc has 3 chapters: 50, 120, 30 chars.

        # With size 10 (40 internal):
        # Ch 1 (50): >40, splits.
        # Ch 2 (120): >40, splits.
        # Ch 3 (30): <40, no split (kept as single chunk).

        if chunk_size == 10:
            # Just verifying we have chunks from all chapters
            chapter_names = {c.metadata.chapter_name for c in chunks}
            assert "Chapter 1" in chapter_names
            assert "Chapter 2" in chapter_names
            assert "Chapter 3" in chapter_names

    def test_data_consistency(self, sample_parsed_doc: ParsedDoc):
        """Verify metadata propagation and ID validity."""
        chunker = MarkdownChunker(chunk_size=10, chunk_overlap=2)
        chunks = chunker.chunk(sample_parsed_doc)

        for chunk in chunks:
            # UUID
            assert isinstance(chunk.metadata.chunk_id, UUID)

            # Source Title
            assert chunk.metadata.source_doc_title == sample_parsed_doc.metadata.title

            # Page Range (should be preserved from chapter)
            # Find the chapter this chunk belongs to
            chapter = next(
                ch
                for ch in sample_parsed_doc.structure.chapters
                if ch.title == chunk.metadata.chapter_name
            )
            assert chunk.metadata.page_range == chapter.page_range

    def test_text_reconstruction(self, sample_parsed_doc: ParsedDoc):
        """Verify that chunks contain expected text."""
        # Use a large chunk size to avoid splitting for this test if possible,
        # or just check specific chunks.

        # Let's use small chunk size to force splitting
        chunker = MarkdownChunker(chunk_size=10, chunk_overlap=2)  # Internal 40
        chunks = chunker.chunk(sample_parsed_doc)

        # Chapter 1 was "A"*50.
        # Split: 0-40 ("A"*40), 32-50 ("A"*18)
        ch1_chunks = [c for c in chunks if c.metadata.chapter_name == "Chapter 1"]
        assert len(ch1_chunks) >= 2
        assert ch1_chunks[0].content == "A" * 40
        assert ch1_chunks[-1].content.endswith("A")

        # Chapter 3 was "C"*30. Should be 1 chunk.
        ch3_chunks = [c for c in chunks if c.metadata.chapter_name == "Chapter 3"]
        assert len(ch3_chunks) == 1
        assert ch3_chunks[0].content == "C" * 30
