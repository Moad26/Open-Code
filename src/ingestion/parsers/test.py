import json
from pathlib import Path

from .get_parser import get_parser

pdf_path = Path("data/Word2Vec.pdf")
print(f"PDF path: {pdf_path}")
print(f"PDF exists: {pdf_path.exists()}")
print(f"PDF absolute path: {pdf_path.absolute()}")

parser = get_parser()
print(f"Parser type: {type(parser)}")

doc_parsed = parser.parse(pdf_path=pdf_path)
print(f"Parsed result type: {type(doc_parsed)}")
print(f"Parsed result: {doc_parsed}")

if doc_parsed is not None:
    with open("output.txt", "w") as f:
        json.dump(doc_parsed.model_dump(), f, indent=2, ensure_ascii=False)
else:
    print("ERROR: Parser returned None")
