import re
from abc import ABC, abstractmethod
from typing import List

from src.shared.models import Chunk, EmbeddedChunk
from src.utils.logger import logger


class TemplateEmbedder(ABC):
    def __init__(self, batch_size: int) -> None:
        self.batch_size = batch_size

    def _preprocess(self, text: str) -> str:
        text.strip()
        text = re.sub(r"\s+", " ", text)
        return text

    @abstractmethod
    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        pass

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        pass

    def embed_chunk(self, chunks: List[Chunk]) -> List[EmbeddedChunk]:
        if not chunks:
            logger.info("No chunks to embed")
            return []

        embedded_chunks: List[EmbeddedChunk] = []
        try:
            for i in range(0, len(chunks), self.batch_size):
                batch = chunks[i : i + self.batch_size]
                logger.debug(
                    f"Embedding batch {i // self.batch_size + 1}/{(len(chunks) - 1) // self.batch_size + 1}"
                )
                processed_texts = [self._preprocess(c.content) for c in chunks]
                valid_indices = [
                    idx for idx, text in enumerate(processed_texts) if text
                ]
                if len(valid_indices) < len(processed_texts):
                    logger.warning(
                        f"Skipping {len(processed_texts) - len(valid_indices)} empty chunks"
                    )

                if not valid_indices:
                    continue
                valid_texts = [processed_texts[idx] for idx in valid_indices]
                valid_chunks = [batch[idx] for idx in valid_indices]

                embeddings = self._embed_batch(valid_texts)
                for chunk, vector in zip(valid_chunks, embeddings):
                    chunk_data = chunk.model_dump()
                    embedded_chunk = EmbeddedChunk(
                        **chunk_data,
                        embedding=vector,
                        vector_id=chunk.metadata.chunk_id,
                    )
                    embedded_chunks.append(embedded_chunk)

            logger.info(f"Successfully embedded {len(embedded_chunks)} chunks")
            return embedded_chunks

        except Exception as e:
            logger.error(f"Failed to embed chunks: {e}")
            raise RuntimeError(f"Embedding failed: {e}")
