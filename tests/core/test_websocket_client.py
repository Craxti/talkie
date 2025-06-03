"""Тесты для WebSocket клиента."""

import json
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from websockets.exceptions import WebSocketException

from talkie.core.websocket_client import WebSocketClient, WebSocketMessage


class AsyncIteratorMock:
    """Мок для асинхронного итератора."""
    def __init__(self, items):
        self.items = items.copy()
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        if not self.items:
            raise WebSocketException("Connection closed")
        return self.items.pop(0)


@pytest.fixture
def mock_websocket():
    """Мок для WebSocket соединения."""
    mock = AsyncMock()
    mock.send = AsyncMock()
    mock.receive = AsyncMock()
    mock.close = AsyncMock()
    return mock


@pytest.mark.asyncio
async def test_websocket_client_init():
    """Тест инициализации WebSocket клиента."""
    client = WebSocketClient(
        uri="ws://example.com",
        headers={"Authorization": "Bearer token"},
        auto_reconnect=True,
        max_reconnect_attempts=3,
        reconnect_interval=0.1
    )
    
    assert client.uri == "ws://example.com"
    assert client.headers == {"Authorization": "Bearer token"}
    assert client.auto_reconnect is True
    assert client.max_reconnect_attempts == 3
    assert client.reconnect_interval == 0.1
    assert client.is_connected is False
    assert client.connection is None


@pytest.mark.asyncio
async def test_websocket_connect_success(mock_websocket):
    """Тест успешного подключения к WebSocket серверу."""
    with patch("websockets.connect", AsyncMock(return_value=mock_websocket)):
        client = WebSocketClient("ws://example.com")
        success = await client.connect()
        
        assert success is True
        assert client.is_connected is True
        assert client.connection == mock_websocket


@pytest.mark.asyncio
async def test_websocket_connect_failure():
    """Тест неудачного подключения к WebSocket серверу."""
    with patch("websockets.connect", AsyncMock(side_effect=WebSocketException("Connection failed"))):
        client = WebSocketClient("ws://example.com")
        success = await client.connect()
        
        assert success is False
        assert client.is_connected is False
        assert client.connection is None


@pytest.mark.asyncio
async def test_websocket_reconnect(mock_websocket):
    """Тест переподключения к WebSocket серверу."""
    connect_mock = AsyncMock(side_effect=[
        WebSocketException("First attempt failed"),
        mock_websocket
    ])
    
    with patch("websockets.connect", connect_mock):
        client = WebSocketClient(
            "ws://example.com",
            auto_reconnect=True,
            max_reconnect_attempts=2,
            reconnect_interval=0.1
        )
        success = await client.reconnect()
        
        assert success is True
        assert client.is_connected is True
        assert connect_mock.call_count == 2


@pytest.mark.asyncio
async def test_websocket_disconnect(mock_websocket):
    """Тест отключения от WebSocket сервера."""
    with patch("websockets.connect", AsyncMock(return_value=mock_websocket)):
        client = WebSocketClient("ws://example.com")
        await client.connect()
        await client.disconnect()
        
        assert client.is_connected is False
        mock_websocket.close.assert_called_once()


@pytest.mark.asyncio
async def test_websocket_send_string(mock_websocket):
    """Тест отправки строкового сообщения."""
    with patch("websockets.connect", AsyncMock(return_value=mock_websocket)):
        client = WebSocketClient("ws://example.com")
        await client.connect()
        
        success = await client.send("Hello, WebSocket!")
        
        assert success is True
        mock_websocket.send.assert_called_once_with("Hello, WebSocket!")


@pytest.mark.asyncio
async def test_websocket_send_dict(mock_websocket):
    """Тест отправки словаря в формате JSON."""
    with patch("websockets.connect", AsyncMock(return_value=mock_websocket)):
        client = WebSocketClient("ws://example.com")
        await client.connect()
        
        message = {"type": "greeting", "content": "Hello"}
        success = await client.send(message)
        
        assert success is True
        mock_websocket.send.assert_called_once_with(json.dumps(message))


@pytest.mark.asyncio
async def test_websocket_send_message_object(mock_websocket):
    """Тест отправки объекта WebSocketMessage."""
    with patch("websockets.connect", AsyncMock(return_value=mock_websocket)):
        client = WebSocketClient("ws://example.com")
        await client.connect()
        
        message = WebSocketMessage(
            type="text",
            data={"content": "Hello"},
            id="msg1"
        )
        success = await client.send(message)
        
        assert success is True
        mock_websocket.send.assert_called_once_with(json.dumps(message.data))


@pytest.mark.asyncio
async def test_websocket_receive(mock_websocket):
    """Тест получения сообщения."""
    # Создаем список сообщений
    messages = ["Hello from server"]
    mock_websocket.__aiter__ = lambda self: AsyncIteratorMock(messages)
    
    with patch("websockets.connect", AsyncMock(return_value=mock_websocket)):
        client = WebSocketClient("ws://example.com")
        await client.connect()
        
        # Ждем, пока сообщение будет обработано
        await asyncio.sleep(0.1)
        
        # Получаем сообщение из очереди
        message = await asyncio.wait_for(client.receive(), timeout=1.0)
        
        assert isinstance(message, WebSocketMessage)
        assert message.type == "text"
        assert message.data == "Hello from server"


@pytest.mark.asyncio
async def test_websocket_event_handlers():
    """Тест обработчиков событий."""
    client = WebSocketClient("ws://example.com")
    
    # Создаем мок-обработчик
    handler = Mock()
    
    # Регистрируем обработчик
    client.on("message", handler)
    
    # Вызываем событие
    await client._trigger_event("message", "test data")
    
    # Проверяем, что обработчик был вызван
    handler.assert_called_once_with("test data")
    
    # Удаляем обработчик
    client.off("message", handler)
    
    # Вызываем событие снова
    await client._trigger_event("message", "test data")
    
    # Проверяем, что обработчик не был вызван второй раз
    handler.assert_called_once()


@pytest.mark.asyncio
async def test_websocket_auto_reconnect_on_connection_closed(mock_websocket):
    """Тест автоматического переподключения при разрыве соединения."""
    # Создаем итераторы для каждого подключения
    messages1 = ["Message before disconnect"]
    messages2 = ["Message after reconnect"]
    
    # Создаем два разных мока для первого подключения и переподключения
    mock_websocket1 = AsyncMock()
    mock_websocket1.__aiter__ = lambda self: AsyncIteratorMock(messages1)
    mock_websocket1.close = AsyncMock()
    
    mock_websocket2 = AsyncMock()
    mock_websocket2.__aiter__ = lambda self: AsyncIteratorMock(messages2)
    mock_websocket2.close = AsyncMock()
    
    # Настраиваем мок для имитации всех попыток подключения:
    # 1. Первое успешное подключение
    # 2-4. Три неудачные попытки после первого разрыва
    # 5-7. Три неудачные попытки после второго разрыва
    connect_mock = AsyncMock(side_effect=[
        mock_websocket1,  # Первое успешное подключение
        WebSocketException("Connection failed"),
        WebSocketException("Connection failed"),
        mock_websocket2,  # Второе успешное подключение
        WebSocketException("Connection failed"),
        WebSocketException("Connection failed"),
        WebSocketException("Connection failed"),
    ])
    
    with patch("websockets.connect", connect_mock):
        client = WebSocketClient(
            "ws://example.com",
            auto_reconnect=True,
            max_reconnect_attempts=3,
            reconnect_interval=0.1
        )
        await client.connect()
        
        # Получаем первое сообщение
        message1 = await asyncio.wait_for(client.receive(), timeout=1.0)
        assert message1.data == "Message before disconnect"
        
        # Ждем, пока соединение закроется и произойдет переподключение
        await asyncio.sleep(0.5)
        
        # Получаем сообщение после переподключения
        message2 = await asyncio.wait_for(client.receive(), timeout=1.0)
        assert message2.data == "Message after reconnect"
        
        # Проверяем, что connect был вызван 7 раз:
        # 1. Первое успешное подключение
        # 2-4. Три неудачные попытки после первого разрыва
        # 5-7. Три неудачные попытки после второго разрыва
        assert connect_mock.call_count == 7


@pytest.mark.asyncio
async def test_websocket_receive_json(mock_websocket):
    """Тест получения JSON сообщения."""
    # Создаем список сообщений
    messages = ['{"type": "test", "data": "Hello"}']
    mock_websocket.__aiter__ = lambda self: AsyncIteratorMock(messages)
    
    with patch("websockets.connect", AsyncMock(return_value=mock_websocket)):
        client = WebSocketClient("ws://example.com")
        await client.connect()
        
        # Ждем, пока сообщение будет обработано
        await asyncio.sleep(0.1)
        
        # Получаем сообщение из очереди
        message = await asyncio.wait_for(client.receive(), timeout=1.0)
        
        assert isinstance(message, WebSocketMessage)
        assert message.type == "json"
        assert message.data == {"type": "test", "data": "Hello"}


@pytest.mark.asyncio
async def test_websocket_receive_binary(mock_websocket):
    """Тест получения бинарного сообщения."""
    # Создаем список сообщений
    messages = [b"Binary data"]
    mock_websocket.__aiter__ = lambda self: AsyncIteratorMock(messages)
    
    with patch("websockets.connect", AsyncMock(return_value=mock_websocket)):
        client = WebSocketClient("ws://example.com")
        await client.connect()
        
        # Ждем, пока сообщение будет обработано
        await asyncio.sleep(0.1)
        
        # Получаем сообщение из очереди
        message = await asyncio.wait_for(client.receive(), timeout=1.0)
        
        assert isinstance(message, WebSocketMessage)
        assert message.type == "binary"
        assert message.data == b"Binary data"


@pytest.mark.asyncio
async def test_websocket_disconnect_error(mock_websocket):
    """Тест ошибки при отключении."""
    mock_websocket.close.side_effect = Exception("Close error")
    
    with patch("websockets.connect", AsyncMock(return_value=mock_websocket)):
        client = WebSocketClient("ws://example.com")
        await client.connect()
        
        # Проверяем, что исключение при закрытии соединения обрабатывается
        await client.disconnect()
        
        # Проверяем, что состояние клиента корректно обновлено
        assert client.is_connected is False
        assert mock_websocket.close.called


@pytest.mark.asyncio
async def test_websocket_receive_error():
    """Тест ошибки при получении сообщения."""
    client = WebSocketClient("ws://example.com")
    
    # Пытаемся получить сообщение без подключения
    try:
        await asyncio.wait_for(client.receive(), timeout=0.1)
        assert False, "Should raise TimeoutError"
    except asyncio.TimeoutError:
        # Это ожидаемое поведение
        pass


@pytest.mark.asyncio
async def test_websocket_stream(mock_websocket):
    """Тест потокового получения сообщений."""
    messages = ["Message 1", "Message 2", "Message 3"]
    mock_websocket.__aiter__ = lambda self: AsyncIteratorMock(messages)
    
    with patch("websockets.connect", AsyncMock(return_value=mock_websocket)):
        client = WebSocketClient("ws://example.com")
        await client.connect()
        
        received_messages = []
        async for message in client.stream():
            received_messages.append(message.data)
            if len(received_messages) == len(messages):
                break
        
        assert received_messages == messages


@pytest.mark.asyncio
async def test_websocket_event_handlers_remove():
    """Тест удаления обработчиков событий."""
    client = WebSocketClient("ws://example.com")
    
    # Создаем мок-обработчики
    handler1 = Mock()
    handler2 = Mock()
    
    # Регистрируем обработчики
    client.on("message", handler1)
    client.on("message", handler2)
    
    # Вызываем событие
    await client._trigger_event("message", "test data")
    
    # Проверяем, что оба обработчика были вызваны
    handler1.assert_called_once_with("test data")
    handler2.assert_called_once_with("test data")
    
    # Удаляем первый обработчик
    client.off("message", handler1)
    
    # Вызываем событие снова
    await client._trigger_event("message", "test data 2")
    
    # Проверяем, что только второй обработчик был вызван
    assert handler1.call_count == 1
    assert handler2.call_count == 2
    
    # Удаляем все обработчики
    client.off("message")
    
    # Вызываем событие снова
    await client._trigger_event("message", "test data 3")
    
    # Проверяем, что обработчики не были вызваны
    assert handler1.call_count == 1
    assert handler2.call_count == 2


@pytest.mark.asyncio
async def test_websocket_connect_exception():
    """Тест исключения при подключении."""
    with patch("websockets.connect", AsyncMock(side_effect=Exception("Connect error"))):
        client = WebSocketClient("ws://example.com")
        success = await client.connect()
        assert success is False


@pytest.mark.asyncio
async def test_websocket_reconnect_max_attempts():
    """Тест максимального количества попыток переподключения."""
    connect_mock = AsyncMock(side_effect=[
        Exception("Connect error"),
        Exception("Connect error"),
        Exception("Connect error"),
    ])
    
    with patch("websockets.connect", connect_mock):
        client = WebSocketClient(
            "ws://example.com",
            auto_reconnect=True,
            max_reconnect_attempts=3,
            reconnect_interval=0.1
        )
        success = await client.reconnect()
        assert success is False
        assert connect_mock.call_count == 3


@pytest.mark.asyncio
async def test_websocket_receive_queue_error():
    """Тест ошибки при получении сообщения из очереди."""
    client = WebSocketClient("ws://example.com")
    
    # Создаем очередь, которая будет бросать исключение
    def queue_get():
        raise Exception("Queue error")
    client._message_queue.get = AsyncMock(side_effect=queue_get)
    
    message = await client.receive()
    assert message is None


@pytest.mark.asyncio
async def test_websocket_trigger_event_error():
    """Тест ошибки в обработчике события."""
    client = WebSocketClient("ws://example.com")
    
    # Создаем обработчик, который будет бросать исключение
    async def error_handler(data):
        raise Exception("Handler error")
    
    # Регистрируем обработчик
    client.on("message", error_handler)
    
    # Вызываем событие
    await client._trigger_event("message", "test data")
    
    # Проверяем, что исключение было обработано
    assert True  # Если мы дошли до этой точки, значит исключение было обработано


@pytest.mark.asyncio
async def test_websocket_receive_binary_with_handler():
    """Тест получения бинарного сообщения с обработчиком."""
    # Создаем список сообщений
    messages = [b"Binary data"]
    mock_websocket = AsyncMock()
    mock_websocket.close = AsyncMock()
    
    # Создаем мок для итератора, который завершится после отправки всех сообщений
    async def mock_aiter(self):
        for message in messages:
            yield message
        raise websockets.exceptions.ConnectionClosed(None, None)
    
    mock_websocket.__aiter__ = mock_aiter
    
    with patch("websockets.connect", AsyncMock(return_value=mock_websocket)):
        client = WebSocketClient("ws://example.com")
        
        # Создаем обработчик для бинарных сообщений
        binary_messages = []
        def binary_handler(message):
            binary_messages.append(message.data)
        
        # Регистрируем обработчик
        client.on("binary", binary_handler)
        
        await client.connect()
        
        # Ждем, пока сообщение будет обработано
        await asyncio.sleep(0.1)
        
        # Закрываем соединение
        await client.disconnect()
        
        # Проверяем, что обработчик был вызван
        assert len(binary_messages) == 1
        assert binary_messages[0] == b"Binary data"


@pytest.mark.asyncio
async def test_websocket_disconnect_with_error():
    """Тест отключения с ошибкой."""
    mock_websocket = AsyncMock()
    mock_websocket.close.side_effect = Exception("Test error")
    
    with patch("websockets.connect", AsyncMock(return_value=mock_websocket)):
        client = WebSocketClient("ws://example.com")
        await client.connect()
        
        # Проверяем, что соединение установлено
        assert client.is_connected is True
        
        # Отключаемся с ошибкой
        await client.disconnect()
        
        # Проверяем, что соединение закрыто несмотря на ошибку
        assert client.is_connected is False
        assert mock_websocket.close.called


@pytest.mark.asyncio
async def test_websocket_reconnect_with_error():
    """Тест переподключения с ошибкой."""
    mock_websocket = AsyncMock()
    mock_websocket.close = AsyncMock()
    
    # Создаем мок для connect, который будет вызывать исключение
    connect_mock = AsyncMock(side_effect=Exception("Test error"))
    
    with patch("websockets.connect", connect_mock):
        client = WebSocketClient("ws://example.com", max_reconnect_attempts=2, reconnect_interval=0.1)
        
        # Пытаемся переподключиться
        result = await client.reconnect()
        
        # Проверяем, что переподключение не удалось
        assert result is False
        assert connect_mock.call_count == 2  # Две попытки переподключения



# @pytest.mark.asyncio
# async def test_websocket_stream_error():
#     """Тест ошибки при стриминге сообщений."""
#     client = WebSocketClient("ws://example.com")
#     client.is_connected = True
    
#     # Создаем очередь, которая будет бросать исключение
#     def queue_get():
#         raise Exception("Queue error")
#     client._message_queue.get = AsyncMock(side_effect=queue_get)
    
#     # Проверяем, что стрим завершается при ошибке
#     messages = []
#     try:
#         async with asyncio.timeout(1.0):
#             async for message in client.stream():
#                 messages.append(message)
#     except asyncio.TimeoutError:
#         pass  # Это ожидаемое поведение
    
#     assert len(messages) == 0
#     assert client.is_connected is True  # Соединение должно остаться активным 