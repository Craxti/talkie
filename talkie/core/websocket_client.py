"""
Module for working with WebSocket connections.

Provides a WebSocket client for establishing and maintaining WebSocket connections,
sending and receiving messages, and subscribing to events.
"""

import json
import asyncio
from typing import Dict, Any, Optional, Callable, List, Union, AsyncGenerator
import websockets
from pydantic import BaseModel
from ..utils.logger import Logger

logger = Logger()


class WebSocketMessage(BaseModel):
    """
    WebSocket message model.
    
    Attributes:
        type (str): Message type (text, binary, ping, pong, close).
        data (Union[str, bytes, dict]): Message data.
        id (Optional[str]): Message identifier.
    """
    type: str
    data: Union[str, bytes, dict]
    id: Optional[str] = None


class WebSocketClient:
    """
    Client for working with WebSocket connections.
    
    The class provides an interface for establishing WebSocket connections,
    sending and receiving messages, and handling events.
    
    Attributes:
        uri (str): WebSocket connection URI.
        headers (Dict[str, str]): Connection headers.
        auto_reconnect (bool): Automatic reconnection on connection loss.
        max_reconnect_attempts (int): Maximum number of reconnection attempts.
        reconnect_interval (float): Interval between reconnection attempts in seconds.
        connection (websockets.WebSocketClientProtocol): WebSocket connection object.
        is_connected (bool): Connection state flag.
        
    Examples:
        >>> async def main():
        ...     client = WebSocketClient("wss://echo.websocket.org")
        ...     await client.connect()
        ...     await client.send("Hello, WebSocket!")
        ...     response = await client.receive()
        ...     print(f"Received: {response}")
        ...     await client.disconnect()
        >>> asyncio.run(main())
    """
    
    def __init__(
        self,
        uri: str,
        headers: Optional[Dict[str, str]] = None,
        auto_reconnect: bool = True,
        max_reconnect_attempts: int = 5,
        reconnect_interval: float = 1.0,
    ):
        """
        Initialize WebSocket client.
        
        Args:
            uri (str): WebSocket connection URI.
            headers (Dict[str, str], optional): Connection headers.
            auto_reconnect (bool): Automatic reconnection on connection loss.
            max_reconnect_attempts (int): Maximum number of reconnection attempts.
            reconnect_interval (float): Interval between reconnection attempts in seconds.
        """
        self.uri = uri
        self.headers = headers or {}
        self.auto_reconnect = auto_reconnect
        self.max_reconnect_attempts = max_reconnect_attempts
        self.reconnect_interval = reconnect_interval
        self.connection = None
        self.is_connected = False
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._message_queue = asyncio.Queue()
        self._background_tasks = set()
    
    async def connect(self) -> bool:
        """
        Establish WebSocket connection.
        
        Returns:
            bool: True if connection was successfully established, False otherwise.
            
        Raises:
            websockets.exceptions.WebSocketException: If connection cannot be established.
        """
        try:
            logger.info(f"Connecting to {self.uri}")
            self.connection = await websockets.connect(
                self.uri, 
                extra_headers=self.headers
            )
            self.is_connected = True
            
            # Start background task for listening to incoming messages
            task = asyncio.create_task(self._listen_for_messages())
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)
            
            logger.info(f"Connection established with {self.uri}")
            return True
        except Exception as e:
            logger.error(f"Error connecting to {self.uri}: {str(e)}")
            return False
    
    async def reconnect(self) -> bool:
        """
        Reconnect to WebSocket server in case of connection loss.
        
        Returns:
            bool: True if reconnection was successful, False otherwise.
        """
        attempt = 0
        while attempt < self.max_reconnect_attempts:
            logger.info(f"Reconnection attempt {attempt + 1}/{self.max_reconnect_attempts}")
            if await self.connect():
                return True
            
            attempt += 1
            await asyncio.sleep(self.reconnect_interval)
        
        logger.error(f"Failed to reconnect after {self.max_reconnect_attempts} attempts")
        return False
    
    async def disconnect(self) -> None:
        """
        Close WebSocket connection.
        """
        if self.connection and self.is_connected:
            logger.info(f"Closing connection to {self.uri}")
            try:
                await self.connection.close()
            except Exception as e:
                logger.error(f"Error closing connection: {str(e)}")
            finally:
                self.is_connected = False
                
                # Cancel all background tasks
                for task in self._background_tasks:
                    task.cancel()
                
                logger.info(f"Connection to {self.uri} closed")
    
    async def send(self, message: Union[str, Dict[str, Any], WebSocketMessage]) -> bool:
        """
        Send message through WebSocket connection.
        
        Args:
            message (Union[str, Dict[str, Any], WebSocketMessage]): Message to send.
                Can be a string, dictionary (which will be converted to JSON) or
                WebSocketMessage object.
                
        Returns:
            bool: True if message was successfully sent, False otherwise.
        """
        if not self.is_connected:
            logger.error("Cannot send message: connection not established")
            return False
        
        try:
            if isinstance(message, WebSocketMessage):
                if isinstance(message.data, dict):
                    await self.connection.send(json.dumps(message.data))
                else:
                    await self.connection.send(message.data)
            elif isinstance(message, dict):
                await self.connection.send(json.dumps(message))
            else:
                await self.connection.send(message)
            
            return True
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            if self.auto_reconnect:
                await self.reconnect()
            return False
    
    async def receive(self) -> Optional[WebSocketMessage]:
        """
        Get message from incoming message queue.
        
        Returns:
            Optional[WebSocketMessage]: Received message or None if error occurred.
        """
        try:
            return await self._message_queue.get()
        except Exception as e:
            logger.error(f"Error receiving message: {str(e)}")
            return None
    
    async def _listen_for_messages(self) -> None:
        """
        Background task for listening to incoming messages.
        Places received messages in queue and calls corresponding event handlers.
        """
        try:
            async for message in self.connection:
                # Determine message type
                if isinstance(message, str):
                    # Try to parse JSON
                    try:
                        data = json.loads(message)
                        msg = WebSocketMessage(type="json", data=data)
                    except json.JSONDecodeError:
                        msg = WebSocketMessage(type="text", data=message)
                else:
                    msg = WebSocketMessage(type="binary", data=message)
                
                # Place message in queue
                await self._message_queue.put(msg)
                
                # Call event handlers
                await self._trigger_event("message", msg)
                await self._trigger_event(msg.type, msg)
                
        except (websockets.exceptions.ConnectionClosed, websockets.exceptions.WebSocketException) as e:
            logger.warning(f"Connection closed: {str(e)}")
            self.is_connected = False
            
            # Call connection close handlers
            close_msg = WebSocketMessage(
                type="close", 
                data={"reason": str(e)}
            )
            await self._trigger_event("close", close_msg)
            
            # Try to reconnect if auto-reconnect is enabled
            if self.auto_reconnect:
                await self.reconnect()
        except Exception as e:
            logger.error(f"Error listening for messages: {str(e)}")
            self.is_connected = False
            
            # Call error handlers
            error_msg = WebSocketMessage(
                type="error", 
                data={"error": str(e)}
            )
            await self._trigger_event("error", error_msg)
    
    async def _trigger_event(self, event_name: str, data: Any) -> None:
        """
        Call handlers for specified event.
        
        Args:
            event_name (str): Event name.
            data (Any): Data passed to handlers.
        """
        handlers = self._event_handlers.get(event_name, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"Error in event handler {event_name}: {str(e)}")
    
    def on(self, event_name: str, handler: Callable) -> None:
        """
        Register event handler.
        
        Args:
            event_name (str): Event name ("message", "close", "error", "json", "text", "binary").
            handler (Callable): Event handler function.
        """
        if event_name not in self._event_handlers:
            self._event_handlers[event_name] = []
        
        self._event_handlers[event_name].append(handler)
    
    def off(self, event_name: str, handler: Optional[Callable] = None) -> None:
        """
        Remove event handler or all handlers for specified event.
        
        Args:
            event_name (str): Event name.
            handler (Optional[Callable]): Handler function to remove.
                If None, all handlers for specified event are removed.
        """
        if event_name not in self._event_handlers:
            return
        
        if handler is None:
            # Remove all handlers for event
            self._event_handlers[event_name] = []
        else:
            # Remove specific handler
            self._event_handlers[event_name] = [
                h for h in self._event_handlers[event_name] if h != handler
            ]
    
    async def stream(self) -> AsyncGenerator[WebSocketMessage, None]:
        """
        Create asynchronous generator for receiving messages in stream mode.
        
        Yields:
            WebSocketMessage: Received messages.
            
        Examples:
            >>> async def process_messages():
            ...     client = WebSocketClient("wss://example.com/ws")
            ...     await client.connect()
            ...     async for message in client.stream():
            ...         print(f"Received: {message.data}")
            >>> asyncio.run(process_messages())
        """
        while self.is_connected:
            try:
                message = await self.receive()
                if message:
                    yield message
            except Exception as e:
                logger.error(f"Error streaming messages: {str(e)}")
                break 