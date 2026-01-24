import pytest
from uuid import uuid4
from src.shared.models import Chunk, ChunkMetadata
from src.ingestion.embedding.base_embed import TemplateEmbedder
from typing import List


@pytest.fixture
def mock_chunks():
    chunks = []
    for i in range(5):
        chunks.append(
            Chunk(
                content=f"This is chunk {i} content. \n It has new lines.",
                metadata=ChunkMetadata(
                    source_doc_title="Test Doc",
                    chapter_name="Test Chapter",
                    page_range=(1, 2),
                    char_span=(0, 100),
                    chunk_id=uuid4(),
                ),
            )
        )
    return chunks


class MockEmbedder(TemplateEmbedder):
    def __init__(self, batch_size=2):
        super().__init__(batch_size)

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        # Mock embedding: return len(text) as a single dimension embedding
        return [[float(len(t))] for t in texts]

    def embed_text(self, text: str) -> List[float]:
        processed = self._preprocess(text)
        return [float(len(processed))]


@pytest.fixture
def mock_template_embedder():
    return MockEmbedder()
