"""Fixtures for MarkdownChunker tests."""

import pytest
from src.shared.models import ParsedDoc, MetaData, DocumentStructure, Chapter


@pytest.fixture
def sample_parsed_doc() -> ParsedDoc:
    """Create a sample ParsedDoc with multiple chapters for testing."""
    # Constructing text to be precise about indices
    # Chapter 1: 50 chars
    c1_text = "A" * 50
    # Chapter 2: 120 chars
    c2_text = "B" * 120
    # Chapter 3: 30 chars
    c3_text = "C" * 30

    full_text = c1_text + c2_text + c3_text

    # Calculate spans
    c1_span = (0, 50)
    c2_span = (50, 170)  # 50 + 120 = 170
    c3_span = (170, 200)  # 170 + 30 = 200

    chapters = [
        Chapter(number=1, title="Chapter 1", page_range=(1, 5), char_span=c1_span),
        Chapter(number=2, title="Chapter 2", page_range=(6, 15), char_span=c2_span),
        Chapter(number=3, title="Chapter 3", page_range=(16, 20), char_span=c3_span),
    ]

    metadata = MetaData(title="Test Document", nbr_pages=20)
    structure = DocumentStructure(chapters=chapters)
    # page_map is required by ParsedDoc validation but not used by Chunker
    page_map = {1: (0, 10)}

    return ParsedDoc(
        text=full_text, metadata=metadata, structure=structure, page_map=page_map
    )
