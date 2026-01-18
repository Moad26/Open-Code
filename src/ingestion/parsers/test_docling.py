from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableStructureOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

input_doc_path = Path("data/Word2Vec.pdf")

# Optimized pipeline - disable unnecessary features
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = False  # ← KEY: PDF already has text!
pipeline_options.do_formula_enrichment = True
# pipeline_options.do_table_structure = False  # ← Disable if you don't need tables
# OR if you need tables:
pipeline_options.do_table_structure = True
pipeline_options.table_structure_options = TableStructureOptions(do_cell_matching=False)

doc_converter = DocumentConverter(
    format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
)

doc = doc_converter.convert(input_doc_path).document
print(doc.export_to_markdown())
