from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Static, Markdown


class UserMessage(Container):
    """A widget to display user messages."""

    def __init__(self, text: str) -> None:
        super().__init__()
        self.text = text

    def compose(self) -> ComposeResult:
        yield Static(self.text, classes="message-content")


class AssistantMessage(Container):
    """A widget to display assistant messages."""

    def __init__(self, text: str) -> None:
        super().__init__()
        self.text = text

    def compose(self) -> ComposeResult:
        yield Markdown(self.text, classes="message-content")
