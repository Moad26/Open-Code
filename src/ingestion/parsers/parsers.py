import os
from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableStructureOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc.document import DoclingDocument

from src.shared.models import Chapter, DocumentStructure, MetaData, ParsedDoc
from src.utils.logger import logger

from .base import BaseParser


class DoclingParser(BaseParser):
    def __init__(self) -> None:
        self.PAGE_BREAK = "<!-- PAGE_BREAK -->"

    def parse(self, pdf_path: os.PathLike) -> ParsedDoc:
        try:
            pdf_path = Path(pdf_path)
            logger.info(f"Starting to parse PDF: {pdf_path}")

            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_ocr = False
            pipeline_options.do_formula_enrichment = True
            pipeline_options.do_table_structure = True
            pipeline_options.table_structure_options = TableStructureOptions(
                do_cell_matching=False
            )

            logger.debug("Initializing DocumentConverter with pipeline options")
            doc_converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                }
            )

            logger.debug("Converting document...")
            result = doc_converter.convert(pdf_path)
            doc = result.document
            logger.info(f"Document converted successfully: {len(doc.pages)} pages")

            logger.debug("Extracting metadata...")
            metadata = self.extract_metadata(doc=doc)
            logger.debug(
                f"Metadata extracted: title='{metadata.title}', pages={metadata.nbr_pages}"
            )

            logger.debug("Exporting to markdown...")
            text = doc.export_to_markdown(page_break_placeholder=self.PAGE_BREAK)
            logger.debug(f"Markdown exported: {len(text)} characters")

            logger.debug("Removing duplicate references...")
            text = self._deduplicate_references(text)

            logger.debug("Building page map...")
            page_map = self._build_page_map(text)
            logger.debug(f"Page map built: {len(page_map)} pages")

            text = text.replace(self.PAGE_BREAK, "")

            logger.debug("Extracting document structure...")
            structure = self._extract_structure_from_markdown(
                text=text, page_map=page_map
            )
            logger.info(f"Structure extracted: {len(structure.chapters)} chapters")

            logger.success(f"Successfully parsed {pdf_path.name}")
            return ParsedDoc(
                text=text, metadata=metadata, structure=structure, page_map=page_map
            )

        except Exception as e:
            logger.error(f"Failed to parse {pdf_path}: {e}")
            raise RuntimeError(
                f"the pdf is not in a good shape, the parser gives this: {e}"
            )

    def extract_metadata(self, doc: DoclingDocument) -> MetaData:
        title = doc.name
        nbr_pages = len(doc.pages)
        return MetaData(title=title or "Unknown", nbr_pages=nbr_pages)

    def _build_page_map(self, text_with_breaks: str) -> dict[int, tuple[int, int]]:
        page_map: dict[int, tuple[int, int]] = {}
        pages = text_with_breaks.split(self.PAGE_BREAK)

        current_pos = 0
        for page_num, page_content in enumerate(pages, start=1):
            page_len = len(page_content)
            page_map[page_num] = (current_pos, current_pos + page_len)
            current_pos += page_len

        return page_map
    def _deduplicate_references(self, text: str) -> str:
        """Remove duplicate reference sections, keeping only the first occurrence"""
        import re
        
        ref_pattern = r'(?:^|\n)((?:References?|Bibliography|REFERENCES?|BIBLIOGRAPHY)\s*\n(?:[-\[\d].*?\n?)+)'
        
        matches = list(re.finditer(ref_pattern, text, re.MULTILINE | re.IGNORECASE))
        
        if len(matches) <= 1:
            return text
        
        # Keep only the first reference section, remove all others
        result = text
        for match in reversed(matches[1:]):  # Process in reverse to maintain positions
            result = result[:match.start()] + result[match.end():]
        
        logger.debug(f"Removed {len(matches) - 1} duplicate reference section(s)")
        return result
    # def _build_page_map(self, doc: DoclingDocument) -> dict[int, tuple[int, int]]:
    #     page_map: dict[int, tuple[int, int]] = {}
    #     min_char, max_char = 0, 0
    #     current_page = 1
    #
    #     for item, _ in doc.iterate_items():
    #         page_nbr = item.prov[0].page_no  # pyright: ignore[reportAttributeAccessIssue]
    #         if current_page < page_nbr:
    #             page_map[current_page] = (min_char, max_char)
    #             min_char = max_char
    #             current_page = page_nbr
    #         # max_char += item.prov[0].charspan[1]  # pyright: ignore[reportAttributeAccessIssue]
    #         max_char += (
    #             item.prov[0].charspan[1] - item.prov[0].charspan[0]  # pyright: ignore[reportAttributeAccessIssue]
    #         )  # Add the length  # pyright: ignore[reportAttributeAccessIssue]
    #
    #     page_map[current_page] = (min_char, max_char)
    #     return page_map

    def _find_page_for_char(
        self, char_pos: int, page_map: dict[int, tuple[int, int]]
    ) -> int:
        for page_num, (start, end) in page_map.items():
            if start <= char_pos < end:
                return page_num
        return max(page_map.keys())

    def _extract_structure_from_markdown(
        self, text: str, page_map: dict[int, tuple[int, int]]
    ) -> DocumentStructure:
        """Extract chapter structure by finding headers in the markdown text."""
        import re

        chapters: list[Chapter] = []

        # Find all markdown headers (# or ## at start of line)
        # Adjust the pattern based on what Docling actually outputs
        header_pattern = r"^#{1,2}\s+(.+)$"

        matches = []
        for match in re.finditer(header_pattern, text, re.MULTILINE):
            header_text = match.group(1).strip()
            char_position = match.start()
            matches.append((header_text, char_position))

        if not matches:
            # Fallback: create single chapter for entire document
            logger.warning("No markdown headers found, creating fallback chapter")
            return DocumentStructure(
                chapters=[
                    Chapter(
                        number=1,
                        title="Full Document",
                        page_range=(1, len(page_map)),
                        char_span=(0, len(text)),
                    )
                ]
            )

        # Build chapters from the matches
        for i, (title, char_start) in enumerate(matches, start=1):
            # char_end is either the next header's start or end of document
            char_end = matches[i][1] if i < len(matches) else len(text)

            # Find which pages this character span covers
            page_start = self._find_page_for_char(char_start, page_map)
            page_end = self._find_page_for_char(char_end - 1, page_map)

            chapters.append(
                Chapter(
                    number=i,
                    title=title,
                    page_range=(page_start, page_end),
                    char_span=(char_start, char_end),
                )
            )
            logger.debug(
                f"Found chapter {i}: '{title}' (chars {char_start}-{char_end})"
            )

        return DocumentStructure(chapters=chapters)

    # def _extract_structure(self, doc: DoclingDocument) -> DocumentStructure:
    #     chapters: list[Chapter] = []
    #     current_chapter_num = 0
    #     current_chapter_title = ""
    #     current_chapter_start_page = 1
    #
    #     for item, level in doc.iterate_items():
    #         label = getattr(item, "label", None)
    #         text = getattr(item, "text", "").strip()
    #         page_nbr = item.prov[0].page_no  # pyright: ignore[reportAttributeAccessIssue]
    #
    #         if not text:
    #             continue
    #
    #         page_start = current_chapter_start_page
    #         page_end = max(current_chapter_start_page, page_nbr - 1)
    #         if label == "section_header":
    #             if current_chapter_num > 0:
    #                 chapters.append(
    #                     Chapter(
    #                         number=current_chapter_num,
    #                         title=current_chapter_title,
    #                         page_range=(page_start, page_end),
    #                     )
    #                 )
    #             current_chapter_num += 1
    #             current_chapter_title = text
    #             current_chapter_start_page = page_nbr
    #             logger.debug(
    #                 f"Found chapter {current_chapter_num}: '{text}' (page {page_nbr})"
    #             )
    #
    #     if current_chapter_num > 0:
    #         page_start = current_chapter_start_page
    #         page_end = len(doc.pages)
    #         chapters.append(
    #             Chapter(
    #                 number=current_chapter_num,
    #                 title=current_chapter_title,
    #                 page_range=(page_start, page_end),
    #             )
    #         )
    #
    #     if not chapters:
    #         logger.warning("No chapters detected, creating fallback chapter")
    #
    #         page_start = 1
    #         page_end = len(doc.pages)
    #         chapters.append(
    #             Chapter(
    #                 number=1, title="Full Document", page_range=(page_start, page_end)
    #             )
    #         )
    #
    #     return DocumentStructure(chapters=chapters)


class MarkerParser(BaseParser):
    def parse(self, pdf_path: os.PathLike) -> ParsedDoc:
        return super().parse(pdf_path)
