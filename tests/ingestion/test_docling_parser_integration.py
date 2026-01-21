"""Integration tests for DoclingParser using real PDF files."""

from pathlib import Path

import pytest

from src.ingestion.parsers.parsers import DoclingParser
from src.shared.models import ParsedDoc


class TestParseIntegration:
    """End-to-end integration tests using actual PDF files."""

    @pytest.mark.slow
    def test_parse_returns_valid_parsed_doc(
        self, parser: DoclingParser, sample_pdf_path: Path
    ) -> None:
        """Verify return type is ParsedDoc and model validates."""
        result = parser.parse(sample_pdf_path)

        assert isinstance(result, ParsedDoc)
        # Pydantic validation passed if we got here
        assert result.text is not None
        assert result.metadata is not None
        assert result.structure is not None
        assert result.page_map is not None

    @pytest.mark.slow
    def test_metadata_page_count_matches_pdf(
        self, parser: DoclingParser, sample_pdf_path: Path
    ) -> None:
        """Verify metadata.nbr_pages matches the actual PDF page count."""
        result = parser.parse(sample_pdf_path)

        # Word2Vec.pdf is known to have a specific number of pages
        # We verify page count is positive and matches page_map
        assert result.metadata.nbr_pages >= 1
        assert result.metadata.nbr_pages == len(result.page_map)

    @pytest.mark.slow
    def test_page_map_keys_match_page_count(
        self, parser: DoclingParser, sample_pdf_path: Path
    ) -> None:
        """Number of keys in page_map equals page count."""
        result = parser.parse(sample_pdf_path)

        assert len(result.page_map) == result.metadata.nbr_pages
        # Verify keys are sequential starting from 1
        expected_keys = set(range(1, result.metadata.nbr_pages + 1))
        assert set(result.page_map.keys()) == expected_keys

    @pytest.mark.slow
    def test_structure_chapters_not_empty(
        self, parser: DoclingParser, sample_pdf_path: Path
    ) -> None:
        """At least one chapter is extracted."""
        result = parser.parse(sample_pdf_path)

        assert len(result.structure.chapters) >= 1
        # Each chapter should have required fields
        for chapter in result.structure.chapters:
            assert chapter.number >= 1
            assert chapter.title
            assert chapter.page_range[0] <= chapter.page_range[1]
            assert chapter.char_span[0] <= chapter.char_span[1]

    @pytest.mark.slow
    def test_last_chapter_char_span_ends_at_text_length(
        self, parser: DoclingParser, sample_pdf_path: Path
    ) -> None:
        """Last chapter's char_span ends at len(text)."""
        result = parser.parse(sample_pdf_path)

        last_chapter = result.structure.chapters[-1]
        assert last_chapter.char_span[1] == len(result.text)

    @pytest.mark.slow
    def test_text_is_non_empty_markdown(
        self, parser: DoclingParser, sample_pdf_path: Path
    ) -> None:
        """Returned text has sufficient length and markdown content."""
        result = parser.parse(sample_pdf_path)

        # Text should have meaningful content
        assert len(result.text) >= 100  # Min from model
        # Should contain some markdown structure (headers, etc.)
        assert result.text.strip()

    @pytest.mark.slow
    def test_page_map_character_ranges_are_valid(
        self, parser: DoclingParser, sample_pdf_path: Path
    ) -> None:
        """Verify page_map character ranges are valid and non-overlapping."""
        result = parser.parse(sample_pdf_path)

        # Verify each page has valid character range
        for page_num, (start, end) in result.page_map.items():
            assert start <= end, f"Page {page_num} has invalid range: {start} > {end}"
            assert start >= 0, f"Page {page_num} has negative start: {start}"

        # Verify pages are contiguous (no gaps between pages)
        sorted_pages = sorted(result.page_map.items())
        for i in range(len(sorted_pages) - 1):
            current_page_end = sorted_pages[i][1][1]
            next_page_start = sorted_pages[i + 1][1][0]
            assert current_page_end == next_page_start, (
                f"Gap between page {sorted_pages[i][0]} and {sorted_pages[i + 1][0]}"
            )

    @pytest.mark.slow
    def test_chapter_page_ranges_within_document(
        self, parser: DoclingParser, sample_pdf_path: Path
    ) -> None:
        """Verify chapter page ranges are within document bounds."""
        result = parser.parse(sample_pdf_path)

        max_page = result.metadata.nbr_pages
        for chapter in result.structure.chapters:
            assert chapter.page_range[0] >= 1, (
                f"Chapter '{chapter.title}' starts before page 1"
            )
            assert chapter.page_range[1] <= max_page, (
                f"Chapter '{chapter.title}' ends after last page"
            )

    @pytest.mark.slow
    def test_metadata_title_is_set(
        self, parser: DoclingParser, sample_pdf_path: Path
    ) -> None:
        """Verify metadata title is extracted."""
        result = parser.parse(sample_pdf_path)

        assert result.metadata.title
        assert result.metadata.title != ""

    @pytest.mark.slow
    def test_chapter_char_spans_within_text(
        self, parser: DoclingParser, sample_pdf_path: Path
    ) -> None:
        """Verify chapter char_spans are within text bounds."""
        result = parser.parse(sample_pdf_path)
        text_len = len(result.text)

        for chapter in result.structure.chapters:
            assert chapter.char_span[0] >= 0, (
                f"Chapter '{chapter.title}' has negative char start"
            )
            assert chapter.char_span[1] <= text_len, (
                f"Chapter '{chapter.title}' char_span exceeds text length"
            )
