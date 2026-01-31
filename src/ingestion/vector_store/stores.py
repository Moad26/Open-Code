from typing import List, Optional, Tuple, cast

import chromadb
from chromadb.api.types import Embedding, Metadata
from redisvl.extensions.cache.llm import SemanticCache

from src.ingestion.embedding.get_embbedder import get_embedder
from src.shared.models import (
    CachedPromptResponse,
    ChunkMetadata,
    EmbeddedChunk,
    SearchResult,
)
from src.utils.config import RedisConfig, VectorStoreConfig, settings
from src.utils.logger import logger


class ChromaStore:
    def __init__(self, config: VectorStoreConfig) -> None:
        self.client_path = config.client_path
        self.collection_name = config.collection_name
        self.client = chromadb.PersistentClient(path=self.client_path)
        try:
            logger.info("creating or getting the collection")
            self.collection = self.client.get_or_create_collection(
                name=config.collection_name
            )
        except Exception as e:
            raise ValueError(f"Probably messed up the  name  huh {e}")
        logger.info("getting the embedder")
        self.embedder = get_embedder()

    def ingest(self, embch: List[EmbeddedChunk]) -> None:
        ids = [str(embed.vector_id) for embed in embch]
        metadatas: List[Metadata] = [
            embed.metadata.model_dump(mode="json") for embed in embch
        ]
        documents = [embed.content for embed in embch]
        embeddings: List[Embedding] = cast(
            List[Embedding], [embed.embedding for embed in embch]
        )
        logger.info("adding chunks to the collection")
        self.collection.add(
            ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas
        )

    def query(self, sentences: List[str], n_result: int) -> List[SearchResult]:
        """
        Returns flat list of SearchResult objects.

        This method queries the vector store with multiple sentences and returns
        a deduplicated, flattened list of all results sorted by score.
        """
        query_embedding = cast(
            List[Embedding],
            self.embedder._embed_batch(sentences),
        )
        logger.info("querying the results")
        results = self.collection.query(
            query_embeddings=query_embedding, n_results=n_result
        )

        all_chunks: List[SearchResult] = []
        seen_ids: set[str] = set()  # Track unique chunks to avoid duplicates

        # Process results for each query
        for i in range(len(results["ids"])):
            assert results["documents"] is not None
            assert results["metadatas"] is not None
            assert results["distances"] is not None
            assert results["ids"] is not None

            current_docs = results["documents"][i]
            current_metas = results["metadatas"][i]
            current_dists = results["distances"][i]
            current_ids = results["ids"][i]

            for doc_id, doc_text, meta_json, score in zip(
                current_ids, current_docs, current_metas, current_dists
            ):
                # Skip duplicates (same chunk returned by multiple queries)
                if doc_id in seen_ids:
                    continue

                seen_ids.add(doc_id)
                metadata = ChunkMetadata.model_validate(meta_json)
                all_chunks.append(
                    SearchResult(content=doc_text, metadata=metadata, score=score)
                )

        # Sort by score (L2 distance - lower is better)
        all_chunks.sort(key=lambda x: x.score)

        logger.info(f"finished the querying - found {len(all_chunks)} unique results")
        return all_chunks

    def count(self) -> int:
        return self.collection.count()
    def clear(self) -> None:
        logger.info(f"Clearing collection '{self.collection_name}'")
        count = self.collection.count()
        if count > 0:
            all_ids = self.collection.get()["ids"]
            self.collection.delete(ids=all_ids)
            logger.info(f"Cleared {count} documents from collection")
        else:
            logger.info("Collection is already empty")

    def delete_collection(self) -> None:
        logger.warning(f"Deleting collection '{self.collection_name}'")
        self.client.delete_collection(name=self.collection_name)
        logger.info(f"Collection '{self.collection_name}' deleted")


class RedisCache:
    def __init__(self, config: RedisConfig) -> None:
        self.host: str = config.host
        self.port: int = config.port
        self.threshold = config.cache_threshold
        self.embedder = get_embedder()
        self.cache = SemanticCache(
            name="book_assistant_cache",
            distance_threshold=self.threshold,
            redis_url=f"redis://{self.host}:{self.port}",
        )

    def store(self, question: str, answer: str) -> None:
        prompt_embedding = self.embedder.embed_text(question)
        self.cache.store(prompt=question, response=answer, vector=prompt_embedding)

    def check(self, prompt: str) -> Optional[List[CachedPromptResponse]]:
        cached_prompt_responses: List[CachedPromptResponse] = []
        prompt_embedding = self.embedder.embed_text(prompt)
        cached_results = self.cache.check(prompt=prompt, vector=prompt_embedding)
        for cached_result in cached_results:
            cached_prompt_response = CachedPromptResponse(
                prompt=cached_result["prompt"], response=cached_result["response"]
            )
            cached_prompt_responses.append(cached_prompt_response)
        return cached_prompt_responses

    def clear(self) -> None:
        self.cache.clear()


def get_store() -> Tuple[ChromaStore, RedisCache]:
    return ChromaStore(settings.vector_store), RedisCache(settings.redis)
