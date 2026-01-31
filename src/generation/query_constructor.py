from abc import ABC, abstractmethod

from .generator import BaseGenerator


class QueryConstructor(ABC):
    @abstractmethod
    def refine_query(self, query: str) -> list[str]:
        """Refine or expand a query into multiple variations."""
        pass


class MultiQueryConstructor(QueryConstructor):
    def __init__(self, generator: BaseGenerator) -> None:
        self.generator = generator
        self.template = """You are a helpful assistant that generates multiple sub-questions related to an input question. \n
        The goal is to break down the input into a set of sub-problems / sub-questions that can be answers in isolation. \n
        Generate multiple search queries related to: {question} \n
        Output (3 queries), one per line:"""

    def refine_query(self, query: str) -> list[str]:
        prompt = self.template.format(question=query)
        response = self.generator.generate(prompt)
        queries = [
            q.strip() for q in response.split("\n") if q.strip() and len(q.strip()) > 10
        ]
        return [query] + queries[:3]
