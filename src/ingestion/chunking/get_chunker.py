from src.ingestion.chunking.base_chunker import BaseChunker
from src.ingestion.chunking.chunker import MarkdownChunker, SemanticChunker
from src.utils.config import settings


def get_chunker() -> BaseChunker:
    chunker_type = settings.chunking.strategy
    if chunker_type == "markdown_based":
        return MarkdownChunker(
            settings.chunking.chunk_size, settings.chunking.chunk_overlap
        )
    elif chunker_type == "semantic":
        return SemanticChunker()
    raise ValueError(f"Unknown chunker: {chunker_type}")
