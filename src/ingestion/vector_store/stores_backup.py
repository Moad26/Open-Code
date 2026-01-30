from typing import List, Optional, cast

import chromadb
from chromadb.api.types import Embedding, Metadata, SearchResult
from redisvl.extensions.cache.llm import SemanticCache

from src.ingestion.embedding.get_embbedder import get_embedder
from src.shared.models import CachedPromptResponse, ChunkMetadata, EmbeddedChunk
from src.utils.config import RedisConfig, VectorStoreConfig
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

    def query(self, sentences: List[str], n_result: int) -> List[List[SearchResult]]:
        query_embedding = cast(
            List[Embedding],
            self.embedder._embed_batch(sentences),
        )
        logger.info("quering the results")
        results = self.collection.query(
            query_embeddings=query_embedding, n_results=n_result
        )
        chunks_output: List[List[SearchResult]] = []

        for i in range(len(results["ids"])):
            query_results: List[SearchResult] = []
            assert results["documents"] is not None
            assert results["metadatas"] is not None
            assert results["distances"] is not None

            current_docs = results["documents"][i]
            current_metas = results["metadatas"][i]
            current_dists = results["distances"][i]

            for doc_text, meta_json, score in zip(
                current_docs, current_metas, current_dists
            ):
                metadata = ChunkMetadata.model_validate(meta_json)

                query_results.append(
                    SearchResult(content=doc_text, metadata=metadata, score=score)
                )

            chunks_output.append(query_results)
        logger.info("finished the quering")
        return chunks_output

    def count(self) -> int:
        return self.collection.count()

    def query_flattened(
        self, sentences: List[str], n_result: int
    ) -> List[SearchResult]:
        """Modified version that returns flat list"""
        query_embedding = cast(
            List[Embedding],
            self.embedder._embed_batch(sentences),
        )
        logger.info("querying the results")
        results = self.collection.query(
            query_embeddings=query_embedding, n_results=n_result
        )

        all_chunks: List[SearchResult] = []

        for i in range(len(results["ids"])):
            assert results["documents"] is not None
            assert results["metadatas"] is not None
            assert results["distances"] is not None

            current_docs = results["documents"][i]
            current_metas = results["metadatas"][i]
            current_dists = results["distances"][i]

            for doc_text, meta_json, score in zip(
                current_docs, current_metas, current_dists
            ):
                metadata = ChunkMetadata.model_validate(meta_json)
                all_chunks.append(
                    SearchResult(content=doc_text, metadata=metadata, score=score)
                )

        logger.info("finished the querying")
        return all_chunks  # Flat list!


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
