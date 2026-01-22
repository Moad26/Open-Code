import os
from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, Field

ROOT_Path = Path(os.getenv("PROJECT_ROOT", Path(__file__).resolve().parent.parent))


class ParsingConfig(BaseModel):
    parser: Literal["marker", "docling"] = Field(
        default="docling", description="PDF parser to use"
    )
    extract_images: bool = Field(
        default=True, description="Extract and store diagrams/figures"
    )
    extract_tables: bool = Field(
        default=True, description="Extract tables as structured data"
    )
    ocr_enabled: bool = Field(
        default=False, description="Use OCR for scanned PDFs (slow)"
    )

    # # Font-based structure detection (for PyMuPDF)
    # heading_font_threshold: float = Field(
    #     default=1.2,
    #     description="Font size multiplier to detect headings (e.g., 1.2x normal = heading)",
    # )
    # code_block_fonts: list[str] = Field(
    #     default=["Courier", "Consolas", "Monaco", "Monospace"],
    #     description="Font families that indicate code blocks",
    # )


class ChunkingConfig(BaseModel):
    strategy: Literal["semantic", "fixed", "hybrid"] = Field(
        default="semantic", description="Chunking strategy"
    )
    chunk_size: int = Field(
        default=512, description="Target chunk size in tokens (for fixed/hybrid)"
    )
    chunk_overlap: int = Field(
        default=50, description="Overlap between chunks in tokens"
    )
    respect_boundaries: bool = Field(
        default=True, description="Never split across section/chapter boundaries"
    )
    min_chunk_size: int = Field(
        default=100, description="Minimum chunk size (discard smaller)"
    )
    max_chunk_size: int = Field(default=1024, description="Hard maximum chunk size")
    # for the semantic chunking
    preserve_code_blocks: bool = Field(
        default=True, description="Keep code listings as atomic chunks"
    )
    preserve_equations: bool = Field(
        default=True, description="Keep equations with surrounding context"
    )


class ConfigModel(BaseModel):
    parsing: ParsingConfig = Field(default_factory=ParsingConfig)
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)


class Config:
    def __init__(self, config_file: os.PathLike = ROOT_Path / "config.yaml"):
        self._file = Path(config_file)
        self._config: Optional[ConfigModel] = None

    @staticmethod
    def save(config: ConfigModel, config_file: os.PathLike):
        with open(config_file, "w") as f:
            yaml.dump(
                config.model_dump(),
                f,
                Dumper=yaml.CDumper,
                default_flow_style=False,
                sort_keys=False,
            )

    def load(self) -> ConfigModel:
        if not self._file.exists():
            self._config = ConfigModel()
            self.save(self._config, self._file)
        else:
            with open(self._file, "r") as f:
                data = yaml.load(f, Loader=yaml.CLoader)
                self._config = ConfigModel(**data)
        return self._config

    @property
    def config(self) -> ConfigModel:
        if self._config is None:
            return self.load()
        return self._config


@lru_cache(maxsize=1)
def get_config() -> ConfigModel:
    return Config().load()


settings = get_config()
