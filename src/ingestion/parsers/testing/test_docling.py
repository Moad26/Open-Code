import logging
from pathlib import Path

from docling.document_converter import DocumentConverter

# input_doc_path = Path("../../../data/Word2Vec.pdf")
#
# # Optimized pipeline - disable unnecessary features
# pipeline_options = PdfPipelineOptions()
# pipeline_options.do_ocr = False  # ← KEY: PDF already has text!
# pipeline_options.do_formula_enrichment = True
# # pipeline_options.do_table_structure = False  # ← Disable if you don't need tables
# # OR if you need tables:
# pipeline_options.do_table_structure = True
# pipeline_options.table_structure_options = TableStructureOptions(do_cell_matching=False)
#
# doc_converter = DocumentConverter(
#     format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
# )
# result = doc_converter.convert(input_doc_path)
# doc: DoclingDocument = result.document
# print(doc.name)
# print(len(doc.pages))

# output_json_file = "Docling_structure.json"
# with open(output_json_file, "w") as f:
#     json.dump(result.document.export_to_dict(), f, indent=2)
#
# print(f"Successfully exported structure to {output_json_file}")
# with open("test_docling_pagemap.txt", "w") as f:
#     for item in doc.iterate_items():
#         print(item, file=f)
# with open("test_docling.txt", "w") as f:
#     print(doc.export_to_markdown(), file=f)
#

# Disable logging
logging.basicConfig(level=logging.ERROR)

source = Path("../../../../data/Word2Vec.pdf")
converter = DocumentConverter()
result = converter.convert(source)
doc = result.document

title_text = ""
headings = []
paragraphs = []

# Iterate over items to categorize them
# We assume the first section_header is the title
found_title = False

for item, level in doc.iterate_items():
    label = getattr(item, "label", None)
    text = getattr(item, "text", "").strip()

    if not text:
        continue

    if label == "section_header":
        # Try to get level from item, default to 1
        h_level = getattr(item, "level", 1)
        headings.append(f"{'#' * h_level} {text}")

        if not found_title:
            title_text = text
            found_title = True

    elif label == "text":
        paragraphs.append(text)

# If no title found from headers, use doc name
if not title_text:
    title_text = doc.name

# Write to files
with open("title.md", "w") as f:
    f.write(title_text + "\n")

with open("headings.md", "w") as f:
    f.write("\n\n".join(headings) + "\n")

with open("paragraphs.md", "w") as f:
    f.write("\n\n".join(paragraphs) + "\n")

print("Extraction complete.")
print(f"Title saved to title.md ({len(title_text)} chars)")
print(f"Headings saved to headings.md ({len(headings)} items)")
print(f"Paragraphs saved to paragraphs.md ({len(paragraphs)} items)")


# page_map: dict[int, tuple[int, int]] = {}
#
# source = Path("../../../data/Word2Vec.pdf")
# converter = DocumentConverter()
# result = converter.convert(source)
# doc = result.document
# maxc, minc, page_prev = 0, 0, 1
# for item, idx in doc.iterate_items():
#     page_nbr = item.prov[0].page_no
#     if page_prev < page_nbr:
#         page_map[page_prev] = (minc, maxc)
#         minc = maxc
#         page_prev += 1
#     maxc += item.prov[0].charspan[1]
# print(page_map)


# items = list(doc.iterate_items())
# item, idx = items[0]
# print("idx", idx)
# print("text", item.text)
# print("text", item.level)
# print("text", item.prov[0].page_no)
# print("text", item.label)
# print("text", item.prov[0].charspan)
# print(item)
