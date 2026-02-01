import typer
from rich.console import Console
from rich.table import Table

from src.ingestion.indexer.manager import LibraryManager
from src.ui.app import RAGApp
from src.utils.config import get_config

app = typer.Typer(
    name="open-books",
    help="Terminal-based RAG assistant for technical books.",
    add_completion=False,
)
console = Console()


@app.command()
def sync():
    """Sync the library: scan books folder and update vector store."""
    config = get_config()
    manager = LibraryManager(config.librery)

    console.print(f"[bold blue]Starting sync process...[/bold blue]")
    # The manager has its own logging, but we could wrap it with specific Rich feedback if we refactor Manager to return generators.
    # For now, we rely on the log output and just trigger the sync.
    manager.sync()

    stats = manager.get_stats()
    console.print(f"[bold green]Sync complete![/bold green]")
    console.print(f"Indexed Files: {stats['indexed_files']}")
    console.print(f"Total Chunks: {stats['total_chunks']}")


@app.command()
def info():
    """Show information about the indexed library."""
    config = get_config()
    manager = LibraryManager(config.librery)

    stats = manager.get_stats()
    manifest = manager.manifest

    table = Table(title="Library Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")

    table.add_row("Total Documents", str(stats["indexed_files"]))
    table.add_row("Total Chunks", str(stats["total_chunks"]))
    table.add_row("Vector Store Path", str(config.vector_store.client_path))

    console.print(table)

    if manifest:
        book_table = Table(title="Indexed Books")
        book_table.add_column("Filename", style="green")
        book_table.add_column("Hash", style="dim", overflow="fold")

        for filename, file_hash in manifest.items():
            book_table.add_row(filename, file_hash)

        console.print(book_table)


@app.command()
def chat():
    """Launch the terminal interactive chat."""
    app = RAGApp()
    app.run()


if __name__ == "__main__":
    app()
