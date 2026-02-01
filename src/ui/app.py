from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, VerticalScroll
from textual.widgets import Footer, Header, Input, Label, ListItem, ListView

from src.generation.answerer import QueryAnswerer
from src.generation.generator import OllamaGenerator
from src.generation.pipeline import SimpleRAGPipeline
from src.ingestion.indexer.manager import LibraryManager
from src.ingestion.vector_store.stores import get_ChromaStore
from src.ui.widgets import AssistantMessage, ThinkingIndicator, UserMessage
from src.utils.config import get_config


class RAGApp(App):
    """The Terminal RAG App."""

    CSS = """
    Screen {
        layout: horizontal;
    }

    #sidebar {
        width: 30;
        dock: left;
        height: 100%;
        background: $panel;
        border-right: vkey $accent;
    }

    #sidebar.hidden {
        display: none;
    }

    #chat-view {
        width: 1fr;
        height: 100%;
        layout: vertical;
    }

    #message-container {
        height: 1fr;
        scrollbar-gutter: stable;
    }

    Input {
        dock: bottom;
        margin: 1 2;
    }

    /* Base message styling */
    UserMessage {
        width: 100%;
        height: auto;
        content-align: right top;
    }

    AssistantMessage {
        width: 100%;
        height: auto;
        content-align: left top;
    }

    /* Content bubble styling */
    .message-content {
        padding: 1 2;
        margin: 1;
        width: auto;
        max-width: 80%;
    }

    UserMessage .message-content {
        background: $primary;
        color: $text;
    }

    AssistantMessage .message-content {
        background: $surface;
        border: solid $primary;
    }

    /* Thinking indicator styling */
    ThinkingIndicator {
        width: 100%;
        height: auto;
        content-align: left top;
        padding: 1;
    }

    ThinkingIndicator LoadingIndicator {
        width: 4;
        height: 1;
    }

    .thinking-text {
        color: $text-muted;
        text-style: italic;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("d", "toggle_dark", "Dark Mode"),
        Binding("s", "toggle_sidebar", "Sidebar"),
        Binding("ctrl+l", "clear_chat", "Clear"),
        Binding("escape", "clear_input", "Clear Input", show=False),
        Binding("pageup", "scroll_page_up", "Scroll Up", show=False),
        Binding("pagedown", "scroll_page_down", "Scroll Down", show=False),
        Binding("up", "scroll_up", show=False),
        Binding("down", "scroll_down", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.config = get_config()
        self.library_manager = LibraryManager(self.config.librery)

        # Initialize pipeline components
        self.vector_store = get_ChromaStore()
        self.generator = OllamaGenerator(self.config.llm)
        self.answerer = QueryAnswerer(self.generator)
        self.pipeline = SimpleRAGPipeline(self.vector_store, self.answerer)

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        # Get stats for subtitle
        stats = self.library_manager.get_stats()
        model_name = self.config.llm.model_name
        subtitle = f"Model: {model_name} | Chunks: {stats['total_chunks']}"

        yield Header()

        with Container(id="sidebar"):
            yield Label("Library", classes="sidebar-title")
            yield ListView(id="book-list")

        with Container(id="chat-view"):
            with VerticalScroll(id="message-container"):
                yield AssistantMessage(
                    "Hello! I'm your technical book assistant. Ask me anything about your library."
                )
            yield Input(placeholder="Type your question here...")

        yield Footer()

    def on_mount(self) -> None:
        """Load books into sidebar on startup and focus input."""
        self.refresh_library()
        # Auto-focus the input
        self.query_one(Input).focus()
        # Update title with stats
        stats = self.library_manager.get_stats()
        model_name = self.config.llm.model_name
        self.sub_title = f"Model: {model_name} | Chunks: {stats['total_chunks']}"

    def refresh_library(self) -> None:
        """Refresh the list of books in the sidebar."""
        book_list = self.query_one("#book-list", ListView)
        book_list.clear()

        manifest = self.library_manager.manifest
        if not manifest:
            book_list.mount(ListItem(Label("No books indexed")))
        else:
            for filename in manifest.keys():
                book_list.mount(ListItem(Label(filename)))

    def action_toggle_sidebar(self) -> None:
        """Toggle sidebar visibility."""
        sidebar = self.query_one("#sidebar")
        sidebar.toggle_class("hidden")

    def action_clear_chat(self) -> None:
        """Clear the chat history."""
        container = self.query_one("#message-container", VerticalScroll)
        container.remove_children()
        container.mount(AssistantMessage("Chat cleared. How can I help you?"))

    def action_clear_input(self) -> None:
        """Clear the input field."""
        input_widget = self.query_one(Input)
        input_widget.value = ""

    @on(Input.Submitted)
    async def handle_input(self, event: Input.Submitted) -> None:
        """Handle user input."""
        query = event.value.strip()
        if not query:
            return

        input_widget = self.query_one(Input)
        input_widget.value = ""

        # Display user message
        container = self.query_one("#message-container", VerticalScroll)
        container.mount(UserMessage(query))

        # Show thinking indicator
        thinking = ThinkingIndicator()
        container.mount(thinking)
        container.scroll_end()

        # Run pipeline in a worker
        self.process_query(query, thinking)

    def action_scroll_page_up(self) -> None:
        """Scroll page up."""
        self.query_one("#message-container", VerticalScroll).scroll_page_up()

    def action_scroll_page_down(self) -> None:
        """Scroll page down."""
        self.query_one("#message-container", VerticalScroll).scroll_page_down()

    def action_scroll_up(self) -> None:
        """Scroll line up."""
        self.query_one("#message-container", VerticalScroll).scroll_up()

    def action_scroll_down(self) -> None:
        """Scroll line down."""
        self.query_one("#message-container", VerticalScroll).scroll_down()

    @work(exclusive=True, thread=True)
    def process_query(self, query: str, thinking: ThinkingIndicator) -> None:
        """Process the query using RAG pipeline in background."""
        container = self.query_one("#message-container", VerticalScroll)

        try:
            answer = self.pipeline.query(query)
            self.call_from_thread(
                lambda: self._display_answer(container, answer, thinking)
            )
        except Exception as e:
            error_msg = f"Error: {e}"
            self.call_from_thread(
                lambda: self._display_answer(container, error_msg, thinking)
            )

    def _display_answer(
        self, container: VerticalScroll, answer: str, thinking: ThinkingIndicator
    ) -> None:
        """Remove thinking indicator and display the answer."""
        thinking.remove()
        container.mount(AssistantMessage(answer))
        container.scroll_end()
