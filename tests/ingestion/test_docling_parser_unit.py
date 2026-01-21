"""Unit tests for DoclingParser with mocking."""

from unittest.mock import MagicMock, patch

import pytest

from src.ingestion.parsers.parsers import DoclingParser
from src.shared.models import DocumentStructure


class TestBuildPageMap:
    """Tests for the _build_page_map method."""

    def test_build_page_map_single_page(self, parser: DoclingParser) -> None:
        """Verify page map with single page content (no page breaks)."""
        text = "Single page content only"
        result = parser._build_page_map(text)

        assert len(result) == 1
        assert result[1] == (0, len(text))

    def test_build_page_map_multiple_pages(
        self, parser: DoclingParser, sample_text_with_breaks: str
    ) -> None:
        """Verify character ranges across multiple pages."""
        result = parser._build_page_map(sample_text_with_breaks)

        assert len(result) == 3
        # Verify page 1 starts at 0
        assert result[1][0] == 0
        # Verify pages are contiguous (each page starts where previous ended)
        assert result[2][0] == result[1][1]
        assert result[3][0] == result[2][1]

    def test_build_page_map_empty_pages(self, parser: DoclingParser) -> None:
        """Edge case: empty page content between breaks."""
        page_break = parser.PAGE_BREAK
        text = f"Content{page_break}{page_break}More content"
        result = parser._build_page_map(text)

        assert len(result) == 3
        # Second page should have zero length
        assert result[2][0] == result[2][1]

    def test_build_page_map_character_positions(self, parser: DoclingParser) -> None:
        """Verify exact character positions are calculated correctly."""
        page_break = parser.PAGE_BREAK
        page1 = "AAAA"  # 4 chars
        page2 = "BBBBBB"  # 6 chars
        page3 = "CC"  # 2 chars
        text = f"{page1}{page_break}{page2}{page_break}{page3}"

        result = parser._build_page_map(text)

        assert result[1] == (0, 4)
        assert result[2] == (4, 10)
        assert result[3] == (10, 12)


class TestFindPageForChar:
    """Tests for the _find_page_for_char method."""

    def test_find_page_for_char_first_page(
        self, parser: DoclingParser, sample_page_map: dict[int, tuple[int, int]]
    ) -> None:
        """Character at start of document should be page 1."""
        result = parser._find_page_for_char(0, sample_page_map)
        assert result == 1

    def test_find_page_for_char_middle_page(
        self, parser: DoclingParser, sample_page_map: dict[int, tuple[int, int]]
    ) -> None:
        """Character in middle of document."""
        # Character at position 150 should be on page 2 (100-250)
        result = parser._find_page_for_char(150, sample_page_map)
        assert result == 2

    def test_find_page_for_char_last_page(
        self, parser: DoclingParser, sample_page_map: dict[int, tuple[int, int]]
    ) -> None:
        """Character at end of document."""
        # Character at position 350 should be on page 3 (250-400)
        result = parser._find_page_for_char(350, sample_page_map)
        assert result == 3

    def test_find_page_for_char_boundary(
        self, parser: DoclingParser, sample_page_map: dict[int, tuple[int, int]]
    ) -> None:
        """Character exactly at page boundary."""
        # Position 100 is start of page 2
        result = parser._find_page_for_char(100, sample_page_map)
        assert result == 2

        # Position 99 is last char of page 1
        result = parser._find_page_for_char(99, sample_page_map)
        assert result == 1

    def test_find_page_for_char_out_of_range(
        self, parser: DoclingParser, sample_page_map: dict[int, tuple[int, int]]
    ) -> None:
        """Out-of-bounds position should return last page."""
        result = parser._find_page_for_char(999, sample_page_map)
        assert result == 3  # Last page


class TestExtractStructureFromMarkdown:
    """Tests for the _extract_structure_from_markdown method."""

    def test_extract_structure_with_headers(
        self,
        parser: DoclingParser,
        sample_page_map: dict[int, tuple[int, int]],
        sample_markdown_with_headers: str,
    ) -> None:
        """Multiple # and ## markdown headers are extracted."""
        result = parser._extract_structure_from_markdown(
            sample_markdown_with_headers, sample_page_map
        )

        assert isinstance(result, DocumentStructure)
        assert len(result.chapters) >= 3  # At least Introduction, Methods, Results

    def test_extract_structure_no_headers(
        self, parser: DoclingParser, sample_page_map: dict[int, tuple[int, int]]
    ) -> None:
        """Fallback chapter when no headers found."""
        text = "This is plain text without any markdown headers at all."
        result = parser._extract_structure_from_markdown(text, sample_page_map)

        assert len(result.chapters) == 1
        assert result.chapters[0].title == "Full Document"
        assert result.chapters[0].char_span == (0, len(text))

    def test_extract_structure_single_header(
        self, parser: DoclingParser, sample_page_map: dict[int, tuple[int, int]]
    ) -> None:
        """Edge case: only one header in document."""
        text = "# Single Header\n\nContent after the header."
        result = parser._extract_structure_from_markdown(text, sample_page_map)

        assert len(result.chapters) == 1
        assert result.chapters[0].title == "Single Header"
        assert result.chapters[0].char_span[1] == len(text)

    def test_extract_structure_char_span_ends_at_text_length(
        self,
        parser: DoclingParser,
        sample_page_map: dict[int, tuple[int, int]],
        sample_markdown_with_headers: str,
    ) -> None:
        """Last chapter's char_span ends at len(text)."""
        result = parser._extract_structure_from_markdown(
            sample_markdown_with_headers, sample_page_map
        )

        last_chapter = result.chapters[-1]
        assert last_chapter.char_span[1] == len(sample_markdown_with_headers)

    def test_extract_structure_chapter_numbers_sequential(
        self,
        parser: DoclingParser,
        sample_page_map: dict[int, tuple[int, int]],
        sample_markdown_with_headers: str,
    ) -> None:
        """Chapter numbers should be sequential starting from 1."""
        result = parser._extract_structure_from_markdown(
            sample_markdown_with_headers, sample_page_map
        )

        for i, chapter in enumerate(result.chapters, start=1):
            assert chapter.number == i

    @pytest.mark.parametrize(
        "markdown,expected_count,expected_first_title",
        [
            ("# H1\nContent\n## H2\nMore", 2, "H1"),
            ("## Only H2\nText here", 1, "Only H2"),
            ("No headers at all", 1, "Full Document"),
            ("# First\n## Second\n# Third\nEnd", 3, "First"),
            ("## Deep\n## Dive\n## Headers", 3, "Deep"),
        ],
    )
    def test_extract_structure_parametrized(
        self,
        parser: DoclingParser,
        sample_page_map: dict[int, tuple[int, int]],
        markdown: str,
        expected_count: int,
        expected_first_title: str,
    ) -> None:
        """Parametrized test for various markdown header scenarios."""
        result = parser._extract_structure_from_markdown(markdown, sample_page_map)

        assert len(result.chapters) == expected_count
        assert result.chapters[0].title == expected_first_title


class TestParseErrorHandling:
    """Tests for error handling in the parse method."""

    def test_parse_error_handling_raises_runtime_error(
        self, parser: DoclingParser
    ) -> None:
        """Mock converter to raise exception, verify RuntimeError is raised."""
        with patch(
            "src.ingestion.parsers.parsers.DocumentConverter"
        ) as mock_converter_class:
            mock_instance = MagicMock()
            mock_converter_class.return_value = mock_instance
            mock_instance.convert.side_effect = Exception("Simulated conversion error")

            with pytest.raises(RuntimeError) as exc_info:
                parser.parse("/fake/path.pdf")

            assert "the pdf is not in a good shape" in str(exc_info.value)
            assert "Simulated conversion error" in str(exc_info.value)

    def test_parse_error_handling_with_file_not_found(
        self, parser: DoclingParser
    ) -> None:
        """Verify error handling when PDF path doesn't exist."""
        with pytest.raises(RuntimeError) as exc_info:
            parser.parse("/nonexistent/path/to/file.pdf")

        assert "the pdf is not in a good shape" in str(exc_info.value)


class TestExtractMetadata:
    """Tests for the extract_metadata method."""

    def test_extract_metadata_with_valid_doc(self, parser: DoclingParser) -> None:
        """Verify metadata extraction from mock DoclingDocument."""
        mock_doc = MagicMock()
        mock_doc.name = "Test Document Title"
        mock_doc.pages = [MagicMock(), MagicMock(), MagicMock()]  # 3 pages

        result = parser.extract_metadata(mock_doc)

        assert result.title == "Test Document Title"
        assert result.nbr_pages == 3

    def test_extract_metadata_with_no_title(self, parser: DoclingParser) -> None:
        """Verify fallback when document has no title."""
        mock_doc = MagicMock()
        mock_doc.name = None
        mock_doc.pages = [MagicMock()]

        result = parser.extract_metadata(mock_doc)

        assert result.title == "Unknown"
        assert result.nbr_pages == 1

    def test_extract_metadata_empty_title(self, parser: DoclingParser) -> None:
        """Verify handling of empty string title."""
        mock_doc = MagicMock()
        mock_doc.name = ""
        mock_doc.pages = [MagicMock(), MagicMock()]

        result = parser.extract_metadata(mock_doc)

        # Empty string is falsy, so should fallback to "Unknown"
        assert result.title == "Unknown"
        assert result.nbr_pages == 2
