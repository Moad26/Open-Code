import pytest
import unittest
from unittest.mock import MagicMock
from src.ingestion.embedding.embedder import SentenceTransformerEmbedder
from src.shared.models import Chunk, ChunkMetadata
from uuid import uuid4


class TestTemplateEmbedder:
    def test_preprocess(self, mock_template_embedder):
        raw_text = "  This   is  a \n test.  "
        expected = "This is a test."
        assert mock_template_embedder._preprocess(raw_text) == expected

    def test_embed_chunk_batching(self, mock_template_embedder, mock_chunks):
        # mock_template_embedder has batch_size=2
        # mock_chunks has 5 chunks

        # We want to ensure that _embed_batch is called 3 times (2, 2, 1)
        # And that result combines them all correctly.

        with unittest.mock.patch.object(
            mock_template_embedder,
            "_embed_batch",
            wraps=mock_template_embedder._embed_batch,
        ) as mock_embed_batch:
            embedded_chunks = mock_template_embedder.embed_chunk(mock_chunks)

            assert mock_embed_batch.call_count == 3
            assert len(embedded_chunks) == 5

            # Check ID mapping
            for i, echunk in enumerate(embedded_chunks):
                assert echunk.vector_id == mock_chunks[i].metadata.chunk_id
                assert len(echunk.embedding) == 1  # From MockEntity implementation

    def test_embed_chunk_empty_handling(self, mock_template_embedder, mocker):
        mock_logger = mocker.patch("src.ingestion.embedding.base_embed.logger")
        empty_chunk = Chunk(
            content="   ",
            metadata=ChunkMetadata(
                source_doc_title="T",
                chapter_name="C",
                page_range=(1, 1),
                char_span=(0, 1),
                chunk_id=uuid4(),
            ),
        )
        chunks = [empty_chunk]

        result = mock_template_embedder.embed_chunk(chunks)
        assert len(result) == 0
        mock_logger.warning.assert_called_with("Skipping 1 empty chunks")


class TestSentenceTransformerEmbedder:
    def test_init_dimension_mismatch(self, mocker):
        mock_st = mocker.patch("src.ingestion.embedding.embedder.SentenceTransformer")
        mock_model = MagicMock()
        mock_model.get_sentence_embedding_dimension.return_value = 768
        mock_st.return_value = mock_model

        with pytest.raises(
            ValueError, match="Model dimension 768 doesn't match config 384"
        ):
            SentenceTransformerEmbedder(expected_dim=384, model_name="test-model")

    def test_embed_batch_calls_model(self, mocker):
        mock_st = mocker.patch("src.ingestion.embedding.embedder.SentenceTransformer")
        mock_model = MagicMock()
        mock_model.get_sentence_embedding_dimension.return_value = 384
        # return numpy array mocked
        mock_model.encode.return_value = MagicMock(tolist=lambda: [[0.1] * 384])
        mock_st.return_value = mock_model

        embedder = SentenceTransformerEmbedder(expected_dim=384)
        res = embedder._embed_batch(["text"])

        assert len(res) == 1
        mock_model.encode.assert_called_once()
