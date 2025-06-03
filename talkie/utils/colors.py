"""Модуль для работы с цветовыми схемами в Talkie."""

from typing import Dict, Tuple

# Стандартные цвета статусов
STATUS_COLORS = {
    # Информационные (1xx)
    100: "blue",
    101: "blue",
    102: "blue",
    103: "blue",
    
    # Успешные (2xx)
    200: "green",
    201: "green",
    202: "green",
    203: "green",
    204: "green",
    205: "green",
    206: "green",
    207: "green",
    208: "green",
    226: "green",
    
    # Перенаправления (3xx)
    300: "yellow",
    301: "yellow",
    302: "yellow",
    303: "yellow",
    304: "yellow",
    305: "yellow",
    306: "yellow",
    307: "yellow",
    308: "yellow",
    
    # Ошибки клиента (4xx)
    400: "red",
    401: "red",
    402: "red",
    403: "red",
    404: "red",
    405: "red",
    406: "red",
    407: "red",
    408: "red",
    409: "red",
    410: "red",
    411: "red",
    412: "red",
    413: "red",
    414: "red",
    415: "red",
    416: "red",
    417: "red",
    418: "red",  # I'm a teapot!
    421: "red",
    422: "red",
    423: "red",
    424: "red",
    425: "red",
    426: "red",
    428: "red",
    429: "red",
    431: "red",
    451: "red",
    
    # Ошибки сервера (5xx)
    500: "magenta",
    501: "magenta",
    502: "magenta",
    503: "magenta",
    504: "magenta",
    505: "magenta",
    506: "magenta",
    507: "magenta",
    508: "magenta",
    510: "magenta",
    511: "magenta",
}

# Цвета для различных типов содержимого
CONTENT_TYPE_COLORS = {
    "application/json": "green",
    "application/xml": "cyan",
    "text/html": "yellow",
    "text/plain": "white",
    "image": "magenta",
    "audio": "blue",
    "video": "blue",
    "application/pdf": "red",
    "application/zip": "yellow",
    "default": "white",
}


def get_status_color(status_code: int) -> str:
    """Получить цвет для статус-кода.
    
    Args:
        status_code: HTTP-статус код
        
    Returns:
        str: Название цвета для Rich
    """
    return STATUS_COLORS.get(status_code, "white")


def get_content_type_color(content_type: str) -> str:
    """Получить цвет для типа содержимого.
    
    Args:
        content_type: MIME-тип содержимого
        
    Returns:
        str: Название цвета для Rich
    """
    for key, color in CONTENT_TYPE_COLORS.items():
        if key in content_type:
            return color
    
    return CONTENT_TYPE_COLORS["default"] 