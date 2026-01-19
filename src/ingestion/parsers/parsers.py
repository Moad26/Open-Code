import os
from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableStructureOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc.document import DoclingDocument

from shared.models import Chapter, DocumentStructure, MetaData, ParsedDoc
from utils.logger import logger  # ← Import your logger

from .base import BaseParser


class DoclingParser(BaseParser):
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
            text = doc.export_to_markdown()
            logger.debug(f"Markdown exported: {len(text)} characters")

            logger.debug("Building page map...")
            page_map = self._build_page_map(doc)
            logger.debug(f"Page map built: {len(page_map)} pages")

            logger.debug("Extracting document structure...")
            structure = self._extract_structure(doc)
            logger.info(f"Structure extracted: {len(structure.chapters)} chapters")

            logger.success(f"✓ Successfully parsed {pdf_path.name}")
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
        for item, _ in doc.iterate_items():
            if getattr(item, "label", None) == "section_header":
                title = getattr(item, "text", "").strip()
                logger.debug(f"Found title from section_header: '{title}'")
                break
        nbr_pages = len(doc.pages)
        return MetaData(title=title or "Unknown", nbr_pages=nbr_pages)

    def _build_page_map(self, doc: DoclingDocument) -> dict[int, tuple[int, int]]:
        page_map: dict[int, tuple[int, int]] = {}
        min_char, max_char = 0, 0
        current_page = 1

        for item, _ in doc.iterate_items():
            page_nbr = item.prov[0].page_no  # pyright: ignore[reportAttributeAccessIssue]
            if current_page < page_nbr:
                page_map[current_page] = (min_char, max_char)
                min_char = max_char
                current_page = page_nbr
            max_char += item.prov[0].charspan[1]  # pyright: ignore[reportAttributeAccessIssue]

        page_map[current_page] = (min_char, max_char)
        return page_map

    def _extract_structure(self, doc: DoclingDocument) -> DocumentStructure:
        chapters: list[Chapter] = []
        current_chapter_num = 0
        current_chapter_title = ""
        current_chapter_start_page = 1

        for item, level in doc.iterate_items():
            label = getattr(item, "label", None)
            text = getattr(item, "text", "").strip()
            page_nbr = item.prov[0].page_no  # pyright: ignore[reportAttributeAccessIssue]

            if not text:
                continue

            if label == "section_header" and level == 0:
                if current_chapter_num > 0:
                    chapters.append(
                        Chapter(
                            number=current_chapter_num,
                            title=current_chapter_title,
                            page_start=current_chapter_start_page,
                            page_end=page_nbr - 1,
                        )
                    )
                current_chapter_num += 1
                current_chapter_title = text
                current_chapter_start_page = page_nbr
                logger.debug(
                    f"Found chapter {current_chapter_num}: '{text}' (page {page_nbr})"
                )

        if current_chapter_num > 0:
            chapters.append(
                Chapter(
                    number=current_chapter_num,
                    title=current_chapter_title,
                    page_start=current_chapter_start_page,
                    page_end=len(doc.pages),
                )
            )

        if not chapters:
            logger.warning("No chapters detected, creating fallback chapter")
            chapters.append(
                Chapter(
                    number=1,
                    title="Full Document",
                    page_start=1,
                    page_end=len(doc.pages),
                )
            )

        return DocumentStructure(chapters=chapters)
