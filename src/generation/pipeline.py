from typing import List

from src.ingestion.vector_store.stores import ChromaStore
from src.shared.models import SearchResult
from src.utils.logger import logger

from .answerer import BaseQueryAnswerer
from .query_constructor import QueryConstructor


class SimpleRAGPipeline:
    def __init__(self, vector_store: ChromaStore, answerer: BaseQueryAnswerer) -> None:
        self.vector_store = vector_store
        self.answerer = answerer

    def query(self, query: str, top_k: int = 5) -> str:
        logger.info(f"Searching for: {query}")

        results: List[SearchResult] = self.vector_store.query([query], n_result=top_k)
        logger.info(f"Found {len(results)} results")

        answer = self.answerer.answer(results, query)
        return answer


class MultiQueryRAGPipeline:
    def __init__(
        self,
        vector_store: ChromaStore,
        answerer: BaseQueryAnswerer,
        query_constructor: QueryConstructor,
    ) -> None:
        self.vector_store = vector_store
        self.answerer = answerer
        self.query_constructor = query_constructor

    def query(self, query: str, top_k: int = 10) -> str:
        # Generate multiple query variations
        queries = self.query_constructor.refine_query(query)
        logger.info(f"Using {len(queries)} query variations")
        logger.info(queries)

        results: List[SearchResult] = self.vector_store.query(queries, n_result=top_k)
        logger.info(f"Found {len(results)} total results")

        answer = self.answerer.answer(results, query)
        return answer
