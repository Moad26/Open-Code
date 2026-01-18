from pydantic import BaseModel, Field, field_validator


class MetaData(BaseModel):
    title: str = Field(default="Unknown", description="The book's name")
    author: str = Field(default="Unknown", description="The author name")
    nbr_pages: int = Field(default=1, description="Da number of PAGES", ge=1)

    @field_validator("title", "author")
    @classmethod
    def validate_not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("field cannot be empty")
        return value.strip()


class Chapter(BaseModel):
    number: int = Field(ge=1)
    title: str
    page_start: int = Field(ge=1)
    page_end: int = Field(ge=1)

    @field_validator("page_end")
    @classmethod
    def validate_page_range(cls, value: int, info) -> int:
        page_start = info.data.get("page_start")
        if page_start and value < page_start:
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
