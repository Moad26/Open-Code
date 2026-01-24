from typing import List

from sentence_transformers import SentenceTransformer

from src.ingestion.embedding.base_embed import TemplateEmbedder
from src.utils.logger import logger


class SentenceTransformerEmbedder(TemplateEmbedder):
    def __init__(
        self,
        expected_dim: int,
        model_name: str = "all-MiniLM-L6-v2",
        batch_size: int = 32,
        device: str = "cpu",
    ):
        super().__init__(batch_size=batch_size)

        logger.info(f"Loading SentenceTransformer model: {model_name}")
        self.model = SentenceTransformer(model_name, device=device)
        self.model_name = model_name
        actual_dim = self.model.get_sentence_embedding_dimension()
        if actual_dim != expected_dim:
            raise ValueError(
                f"Model dimension {actual_dim} doesn't match config {expected_dim}"
            )
        logger.info(f"Model loaded: {actual_dim}d on {self.model.device}")

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        try:
            embeddings = self.model.encode(
                texts,
                batch_size=self.batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            raise

    def embed_text(self, text: str) -> List[float]:
        preprocessed = self._preprocess(text)
        if not preprocessed:
            raise ValueError("Cannot embed empty text")

        try:
            embedding = self.model.encode(preprocessed, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Text embedding failed: {e}")
            raise

    @property
    def embedding_dim(self) -> int:
        embed_dim = self.model.get_sentence_embedding_dimension()
        if embed_dim is None:
            raise ValueError("embed_dim must not be None")
        return embed_dim
