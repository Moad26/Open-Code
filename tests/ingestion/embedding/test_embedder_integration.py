import pytest
from src.ingestion.embedding.embedder import SentenceTransformerEmbedder
from src.ingestion.embedding.get_embbedder import get_embedder
from src.shared.models import Chunk, ChunkMetadata, EmbeddedChunk
from uuid import uuid4
from unittest.mock import MagicMock


@pytest.mark.integration
class TestEmbedderIntegration:
    def test_real_inference_flow(self):
        # Using a very small model for integration test
        # We use a mocked name in unit tests, but here we want a real one.
        # However, to avoid huge downloads during tests, we might want to skip if no internet or model not found?
        # But the prompt asks for it. unique small model: "paraphrase-albert-small-v2"

        try:
            embedder = SentenceTransformerEmbedder(
                expected_dim=768,  # paraphrase-albert-small-v2 has 768 dim
                model_name="paraphrase-albert-small-v2",
                batch_size=2,
            )
        except Exception as e:
            pytest.skip(f"Skipping integration test due to model loading failure: {e}")

        chunk = Chunk(
            content="Hello world integration test",
            metadata=ChunkMetadata(
                source_doc_title="Doc",
                chapter_name="Chap",
                page_range=(1, 1),
                char_span=(0, 10),
                chunk_id=uuid4(),
            ),
        )

        results = embedder.embed_chunk([chunk])

        assert len(results) == 1
        assert isinstance(results[0], EmbeddedChunk)
        assert len(results[0].embedding) == 768
        assert results[0].vector_id == chunk.metadata.chunk_id

    def test_factory_test(self, mocker):
        mock_settings = mocker.patch("src.ingestion.embedding.get_embbedder.settings")
        mock_settings.embedding.provider = "sentence_transformers"
        mock_settings.embedding.dimensions = 384
        mock_settings.embedding.model_name = "test-factory-model"
        mock_settings.embedding.batch_size = 16
        mock_settings.embedding.device = "cpu"

        # We need to mock SentenceTransformer constructor inside the factory call to avoid real load
        mocker.patch("src.ingestion.embedding.embedder.SentenceTransformer")
        # We also need to mock the dim check
        mock_st_class = mocker.patch(
            "src.ingestion.embedding.embedder.SentenceTransformer"
        )
        mock_st_instance = MagicMock()
        mock_st_instance.get_sentence_embedding_dimension.return_value = 384
        mock_st_class.return_value = mock_st_instance

        embedder = get_embedder()
        assert isinstance(embedder, SentenceTransformerEmbedder)
        assert embedder.batch_size == 16
        assert embedder.model_name == "test-factory-model"
