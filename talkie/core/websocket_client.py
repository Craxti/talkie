"""WebSocket client for real-time communication."""

from typing import Any, Optional, Callable


class WebSocketMessage:
    """WebSocket message model."""

    def __init__(self, message_type: str, data: Any, message_id: Optional[str] = None):
        self.type = message_type
        self.data = data
        self.id = message_id


class WebSocketClient:
    """WebSocket client."""

    def __init__(self, uri: str):
        self.uri = uri
        self.connection = None
        self.is_connected = False
        self._handlers = {}

    async def connect(self) -> bool:
        """Connect to WebSocket server."""
        try:
            # Mock connection for now
            self.is_connected = True
            return True
        except (ConnectionError, OSError) as e:
            print(f"Connection failed: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from WebSocket server."""
        self.is_connected = False

    async def send(self, message: str) -> bool:
        """Send message."""
        if not self.is_connected:
            return False
        # Mock send
        return True

    async def receive(self) -> Optional[WebSocketMessage]:
        """Receive message."""
        if not self.is_connected:
            return None
        # Mock receive
        return WebSocketMessage("text", "mock message")

    def on(self, event: str, handler: Callable) -> None:
        """Register event handler."""
        if event not in self._handlers:
            self._handlers[event] = []
        self._handlers[event].append(handler)
