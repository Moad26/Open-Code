from typing import Tuple, Union
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer, field_validator


class MetaData(BaseModel):
    title: str = Field(default="Unknown", description="The book's name")
    nbr_pages: int = Field(default=1, description="Da number of PAGES", ge=1)

    @field_validator("title")
    @classmethod
    def validate_not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("field cannot be empty")
        return value.strip()


class Chapter(BaseModel):
    number: int = Field(ge=1)
    title: str
    page_range: Tuple[int, int] = Field(description="Start and end page numbers")
    char_span: Tuple[int, int] = Field(description="da span of char")

    @field_validator("page_range", "char_span", mode="before")
    @classmethod
    def deserialize_tuple(cls, value: Union[Tuple[int, int], str]) -> Tuple[int, int]:
        if isinstance(value, str):
            start, end = value.split("-")
            return (int(start), int(end))
        return value

    @field_validator("page_range", "char_span")
    @classmethod
    def validate_page_range(cls, value: Tuple[int, int]) -> Tuple[int, int]:
        page_start, page_end = value
        if page_end < page_start:
            raise ValueError("it's ironic u see")
        return value

    @field_serializer("page_range", "char_span")
    def serialize_tuple(self, value: Tuple[int, int]) -> str:
        return f"{value[0]}-{value[1]}"


class DocumentStructure(BaseModel):
    chapters: list[Chapter] = Field(min_length=1)


class ParsedDoc(BaseModel):
    text: str = Field(description="The text in markdown format", min_length=100)
    metadata: MetaData = Field(description="Global metadata of the book")
    structure: DocumentStructure = Field(
        description="The document's hierarchical structure"
    )
    page_map: dict[int, tuple[int, int]] = Field(
        description="Maps page number to (start_char, end_char)", min_length=1
    )

    @field_serializer("page_map")
    def serialize_page_map(self, value: dict[int, tuple[int, int]]) -> dict[int, str]:
        return {page: f"{span[0]}-{span[1]}" for page, span in value.items()}


class ChunkMetadata(BaseModel):
    source_doc_title: str = Field(description="The source document title")
    chapter_name: str = Field(description="The chapter name")
    page_range: Tuple[int, int] = Field(description="Start and end page numbers")
    char_span: Tuple[int, int] = Field(description="span of charactres ig")
    chunk_id: UUID = Field(description="its understadable ig")

    @field_validator("page_range", "char_span", mode="before")
    @classmethod
    def deserialize_tuple(cls, value: Union[Tuple[int, int], str]) -> Tuple[int, int]:
        if isinstance(value, str):
            start, end = value.split("-")
            return (int(start), int(end))
        return value

    @field_serializer("page_range", "char_span")
    def serialize_tuple(self, value: Tuple[int, int]) -> str:
        return f"{value[0]}-{value[1]}"


class Chunk(BaseModel):
    content: str = Field(description="same same but differeeent")
    metadata: ChunkMetadata = Field(description="but still same")


class EmbeddedChunk(Chunk):
    embedding: list[float] = Field(
        description="the embedding of the content of the chunk"
    )
    vector_id: UUID = Field(description="it's understadable ig")


class SearchResult(Chunk):
    score: float = Field(description="Similarity score (closer to 0 is better for L2)")


class CachedPromptResponse(BaseModel):
    prompt: str = Field(description="da prompt")
    response: str = Field(description="da resp")
