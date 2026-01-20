from typing import Tuple
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


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

    @field_validator("page_range")
    @classmethod
    def validate_page_range(cls, value: Tuple[int, int]) -> Tuple[int, int]:
        page_start, page_end = value
        if page_end < page_start:
            raise ValueError("page_end must be >= page_start")
        return value


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


class ChunkMetadata(BaseModel):
    source_doc_title: str = Field(description="The source document title")
    chapter_name: str = Field(description="The chapter name")
    page_range: Tuple[int, int] = Field(description="Start and end page numbers")
    char_span: Tuple[int, int] = Field(description="span of charactres ig")
    chunk_id: UUID = Field(description="its understadable ig")


class Chunk(BaseModel):
    content: str = Field(description="same same but differeeent")
    metadata: ChunkMetadata = Field(description="but still same")
