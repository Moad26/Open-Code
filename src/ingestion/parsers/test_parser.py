"""
Test script for DoclingParser to verify:
1. Metadata extraction
2. Page map building
3. Chapter structure extraction with char_span
4. Text export
"""

from pathlib import Path

from src.ingestion.parsers.parsers import DoclingParser


def test_parser():
    # Path to your test PDF
    pdf_path = Path("data/Word2Vec.pdf")

    if not pdf_path.exists():
        print(f"❌ PDF not found: {pdf_path}")
        return

    print("=" * 60)
    print("🧪 TESTING DOCLING PARSER")
    print("=" * 60)

    # Initialize parser
    parser = DoclingParser()

    # Parse the PDF
    print(f"\n📄 Parsing: {pdf_path.name}")
    result = parser.parse(pdf_path)

    # ===== TEST 1: METADATA =====
    print("\n" + "=" * 60)
    print("📊 METADATA")
    print("=" * 60)
    print(f"Title: {result.metadata.title}")
    print(f"Number of pages: {result.metadata.nbr_pages}")

    # ===== TEST 2: PAGE MAP =====
    print("\n" + "=" * 60)
    print("🗺️  PAGE MAP")
    print("=" * 60)
    print(f"Total pages in map: {len(result.page_map)}")
    print("\nFirst 5 pages:")
    for page_num in sorted(result.page_map.keys())[:5]:
        start, end = result.page_map[page_num]
        char_count = end - start
        print(f"  Page {page_num}: chars {start:,}-{end:,} ({char_count:,} chars)")

    # Verify page_map consistency
    last_page = max(result.page_map.keys())
    max_char = result.page_map[last_page][1]
    text_len = len(result.text)

    print("\nPage map validation:")
    print(f"  Max char in page_map: {max_char:,}")
    print(f"  Text length: {text_len:,}")
    print(f"  Match: {'✅ YES' if abs(max_char - text_len) < 100 else '❌ NO'}")

    # ===== TEST 3: CHAPTER STRUCTURE =====
    print("\n" + "=" * 60)
    print("📖 CHAPTER STRUCTURE")
    print("=" * 60)
    print(f"Total chapters detected: {len(result.structure.chapters)}")

    if (
        len(result.structure.chapters) == 1
        and result.structure.chapters[0].title == "Full Document"
    ):
        print("⚠️  WARNING: Only fallback chapter detected!")
        print("   This means no markdown headers were found.")
    else:
        print("\nChapters:")
        for ch in result.structure.chapters:
            page_start, page_end = ch.page_range
            char_start, char_end = ch.char_span
            page_range_str = f"pages {page_start}-{page_end}"
            page_count = page_end - page_start + 1
            char_count = char_end - char_start
            print(f"  {ch.number}. {ch.title}")
            print(f"     {page_range_str} ({page_count} pages)")
            print(f"     chars {char_start:,}-{char_end:,} ({char_count:,} chars)")

    # ===== TEST 4: TEXT EXPORT =====
    print("\n" + "=" * 60)
    print("📝 TEXT EXPORT")
    print("=" * 60)
    print(f"Total characters: {len(result.text):,}")
    print("\nFirst 500 characters:")
    print("-" * 60)
    print(result.text[:500])
    print("-" * 60)

    # ===== TEST 5: SAMPLE PAGE EXTRACTION =====
    print("\n" + "=" * 60)
    print("📄 SAMPLE PAGE EXTRACTION")
    print("=" * 60)

    # Extract page 1 using page_map
    if 1 in result.page_map:
        start, end = result.page_map[1]
        page_1_text = result.text[start:end]
        print(f"Page 1 content ({len(page_1_text)} chars):")
        print("-" * 60)
        print(page_1_text[:300])
        print("-" * 60)

    # ===== TEST 6: CHAPTER VALIDATION =====
    print("\n" + "=" * 60)
    print("✅ CHAPTER VALIDATION")
    print("=" * 60)

    # Check if chapters have valid page ranges and char spans
    all_valid = True
    for ch in result.structure.chapters:
        page_start, page_end = ch.page_range
        char_start, char_end = ch.char_span

        page_valid = page_start <= page_end <= result.metadata.nbr_pages
        char_valid = 0 <= char_start < char_end <= len(result.text)
        is_valid = page_valid and char_valid

        status = "✅" if is_valid else "❌"
        print(
            f"{status} Chapter {ch.number}: pages {page_start}-{page_end}, chars {char_start:,}-{char_end:,}"
        )
        if not is_valid:
            all_valid = False
            if not page_valid:
                print("   ⚠️  Invalid page range")
            if not char_valid:
                print("   ⚠️  Invalid char span")

    print(f"\nAll chapters valid: {'✅ YES' if all_valid else '❌ NO'}")

    # ===== TEST 7: CHAR_SPAN CONSISTENCY =====
    print("\n" + "=" * 60)
    print("🔍 CHAR_SPAN CONSISTENCY CHECK")
    print("=" * 60)

    # Verify char_spans are contiguous and cover the whole document
    sorted_chapters = sorted(result.structure.chapters, key=lambda x: x.char_span[0])

    print("Checking if chapters are contiguous...")
    for i in range(len(sorted_chapters) - 1):
        current_end = sorted_chapters[i].char_span[1]
        next_start = sorted_chapters[i + 1].char_span[0]
        gap = next_start - current_end

        if gap == 0:
            print(
                f"✅ Chapter {sorted_chapters[i].number} → {sorted_chapters[i + 1].number}: contiguous"
            )
        else:
            print(
                f"⚠️  Chapter {sorted_chapters[i].number} → {sorted_chapters[i + 1].number}: gap of {gap} chars"
            )

    # Check coverage
    first_char = sorted_chapters[0].char_span[0]
    last_char = sorted_chapters[-1].char_span[1]
    print("\nDocument coverage:")
    print(f"  First chapter starts at: {first_char:,}")
    print(f"  Last chapter ends at: {last_char:,}")
    print(f"  Document length: {len(result.text):,}")
    print(
        f"  Coverage: {'✅ Complete' if first_char == 0 and last_char == len(result.text) else '⚠️  Incomplete'}"
    )

    # ===== TEST 8: EXTRACT CHAPTERS USING CHAR_SPAN =====
    print("\n" + "=" * 60)
    print("📚 CHAPTER EXTRACTION USING CHAR_SPAN")
    print("=" * 60)

    for ch in result.structure.chapters[:3]:  # First 3 chapters
        char_start, char_end = ch.char_span
        chapter_text = result.text[char_start:char_end]

        print(f"\nChapter {ch.number}: {ch.title}")
        print(f"  Char span: {char_start:,}-{char_end:,}")
        print(f"  Length: {len(chapter_text):,} chars")
        print("  Preview (first 200 chars):")
        print("  " + "-" * 58)
        print("  " + chapter_text[:200].replace("\n", "\n  "))
        print("  " + "-" * 58)

    # ===== SUMMARY =====
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print("✅ Parsed successfully")
    print(f"✅ {result.metadata.nbr_pages} pages")
    print(f"✅ {len(result.page_map)} page map entries")
    print(f"✅ {len(result.structure.chapters)} chapters")
    print(f"✅ {len(result.text):,} characters")

    # Save output for inspection
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)

    # Save first chapter text using char_span
    if result.structure.chapters:
        ch1 = result.structure.chapters[0]
        char_start, char_end = ch1.char_span
        ch1_text = result.text[char_start:char_end]

        output_file = output_dir / "chapter_1.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"# {ch1.title}\n\n")
            page_start, page_end = ch1.page_range
            f.write(f"Pages: {page_start}-{page_end}\n")
            f.write(f"Characters: {char_start:,}-{char_end:,}\n\n")
            f.write(ch1_text)
        print(f"\n💾 Saved Chapter 1 to: {output_file}")

    print("\n" + "=" * 60)
    print("✅ TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    test_parser()
