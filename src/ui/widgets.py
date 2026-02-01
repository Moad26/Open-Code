from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static, Markdown, LoadingIndicator


class UserMessage(Container):
    """A widget to display user messages."""

    def __init__(self, text: str) -> None:
        super().__init__()
        self.text = text

    def compose(self) -> ComposeResult:
        yield Static(self.text, classes="message-content")


class AssistantMessage(Container):
    """A widget to display assistant messages with Markdown support."""

    def __init__(self, text: str) -> None:
        super().__init__()
        self.text = text

    def compose(self) -> ComposeResult:
        yield Markdown(self.text, classes="message-content")


class ThinkingIndicator(Container):
    """A widget to show that the assistant is thinking."""

    def compose(self) -> ComposeResult:
        yield LoadingIndicator()
        yield Static("Thinking...", classes="thinking-text")
