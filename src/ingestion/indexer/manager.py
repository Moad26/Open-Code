"""Library management for syncing PDFs to vector store."""

import hashlib
import json
from pathlib import Path
from typing import Dict

from src.ingestion.chunking.get_chunker import get_chunker
from src.ingestion.embedding.get_embbedder import get_embedder
from src.ingestion.parsers.get_parser import get_parser
from src.ingestion.vector_store.stores import get_ChromaStore
from src.utils.config import LibreryConfig
from src.utils.logger import logger


class LibraryManager:
    def __init__(self, config: LibreryConfig) -> None:
        self.books_dir = Path(config.books_paths)
        self.manifest_path = Path(config.manifest_path)

        logger.info("Initializing LibraryManager...")

        self.store = get_ChromaStore()
        self.parser = get_parser()
        self.chunker = get_chunker()

        self.manifest = self._load_manifest()
        logger.info(f"Loaded manifest with {len(self.manifest)} entries")

    def _load_manifest(self) -> Dict[str, str]:
        if self.manifest_path.exists():
            try:
                return json.loads(self.manifest_path.read_text())
            except Exception as e:
                logger.warning(f"Failed to load manifest: {e}. Starting fresh.")
                return {}
        return {}

    def _save_manifest(self) -> None:
        try:
            self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
            self.manifest_path.write_text(json.dumps(self.manifest, indent=2))
            logger.debug("Manifest saved")
        except Exception as e:
            logger.error(f"Failed to save manifest: {e}")

    def _calculate_hash(self, file_path: Path) -> str:
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    def sync(self) -> None:
        logger.info(f"Starting sync from: {self.books_dir}")

        current_files = list(self.books_dir.glob("*.pdf"))
        logger.info(f"Found {len(current_files)} PDF files")

        if not current_files:
            logger.warning("No PDF files found in books directory")
            return

        found_filenames = {f.name for f in current_files}

        self._cleanup_deleted_files(found_filenames)

        self._process_files(current_files)

        self._save_manifest()

        logger.success(f"Sync complete! Vector store has {self.store.count()} chunks")

    def _cleanup_deleted_files(self, found_filenames: set) -> None:
        for filename in list(self.manifest.keys()):
            if filename not in found_filenames:
                logger.info(f"File removed: {filename}")
                try:
                    self.store.delete_by_filename(filename)
                    del self.manifest[filename]
                    logger.info(f"Cleaned up {filename} from index")
                except Exception as e:
                    logger.error(f"Failed to clean up {filename}: {e}")

    def _process_files(self, current_files: list) -> None:
        total = len(current_files)

        for idx, file_path in enumerate(current_files, 1):
            name = file_path.name
            logger.info(f"\n[{idx}/{total}] Processing: {name}")

            try:
                logger.debug(f"Calculating hash for {name}...")
                current_hash = self._calculate_hash(file_path)

                if self.manifest.get(name) == current_hash:
                    logger.info(f"Skipping {name} (unchanged)")
                    continue

                if name in self.manifest:
                    logger.info(f"Content changed: {name}")
                    self.store.delete_by_filename(name)
                else:
                    logger.info(f"New file: {name}")

                self._index_file(file_path, name, current_hash)

            except Exception as e:
                logger.error(f"Failed to process {name}: {e}")
                logger.exception("Full traceback:")

    def _index_file(self, file_path: Path, name: str, file_hash: str) -> None:
        logger.info(f"Parsing {name}...")
        parsed_doc = self.parser.parse(file_path)
        logger.info(f"Parsed {parsed_doc.metadata.nbr_pages} pages")

        logger.info(f"Chunking {name}...")
        chunked_doc = self.chunker.chunk(parsed_doc)
        logger.info(f"Created {len(chunked_doc)} chunks")

        logger.info(f"Storing {name}...")
        self.store.ingest(chunks=chunked_doc)
        logger.info(f"Stored in vector DB")

        self.manifest[name] = file_hash
        logger.success(f"Successfully indexed: {name}")

    def get_stats(self) -> Dict[str, int]:
        return {
            "indexed_files": len(self.manifest),
            "total_chunks": self.store.count(),
        }

    def force_reindex(self, filename: str) -> None:
        logger.info(f"Force reindexing: {filename}")

        file_path = self.books_dir / filename
        if not file_path.exists():
            logger.error(f"File not found: {filename}")
            return

        if filename in self.manifest:
            self.store.delete_by_filename(filename)
            del self.manifest[filename]

        current_hash = self._calculate_hash(file_path)
        self._index_file(file_path, filename, current_hash)
        self._save_manifest()

    def clear_all(self) -> None:
        logger.warning("Clearing all indexed data...")
        self.store.clear()
        self.manifest = {}
        self._save_manifest()
        logger.success("All data cleared")
