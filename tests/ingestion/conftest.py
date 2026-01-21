"""Shared fixtures for DoclingParser tests."""

from pathlib import Path

import pytest

from src.ingestion.parsers.parsers import DoclingParser


@pytest.fixture
def parser() -> DoclingParser:
    """Provide a fresh DoclingParser instance for each test."""
    return DoclingParser()


@pytest.fixture
def sample_pdf_path() -> Path:
    """Provide the path to the sample PDF for integration tests."""
    path = Path(__file__).parent.parent.parent / "data" / "Word2Vec.pdf"
    if not path.exists():
        pytest.skip(f"Sample PDF not found: {path}")
    return path


@pytest.fixture
def sample_page_map() -> dict[int, tuple[int, int]]:
    """Provide a pre-defined page map for unit testing."""
    return {
        1: (0, 100),
        2: (100, 250),
        3: (250, 400),
    }


@pytest.fixture
def sample_text_with_breaks(parser: DoclingParser) -> str:
    """Sample markdown text with page breaks for testing _build_page_map."""
    page_break = parser.PAGE_BREAK
    return (
        f"Page 1 content here{page_break}Page 2 has more text{page_break}Final page 3"
    )


@pytest.fixture
def sample_markdown_with_headers() -> str:
    """Sample markdown with headers for structure extraction tests."""
    return """# Introduction

This is the introduction section with some content.

## Background

Here we discuss the background of the topic.

# Methods

The methodology section describes our approach.

## Data Collection

Details about data collection process.

## Analysis

How we analyzed the data.

# Results

The results of our study are presented here.
"""
