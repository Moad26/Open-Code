from abc import ABC, abstractmethod
from typing import List

from src.generation.generator import BaseGenerator
from src.shared.models import SearchResult


class BaseQueryAnswerer(ABC):
    """Abstract base class for query answerers."""

    @abstractmethod
    def answer(self, result_search: List[SearchResult], query: str) -> str:
        """Generate answer from search results and query."""
        pass


class QueryAnswerer(BaseQueryAnswerer):
    """Generates answers using LLM with retrieved context."""

    def __init__(self, generator: BaseGenerator) -> None:
        self.generator = generator
        self.template = """Answer this question using only the context below.

        Context:
        {context}

        Question: {question}

        Answer:"""

    def answer(self, result_search: List[SearchResult], query: str) -> str:
        if not result_search:
            return "No relevant documents found."

        context_parts = [f"[{i}] {r.content}" for i, r in enumerate(result_search, 1)]
        context = "\n\n".join(context_parts)
        print(context)
        prompt = self.template.format(context=context, question=query)
        return self.generator.generate(prompt).strip()
