import json
from typing import List

from models import Pizza
from openai_client import ask_chatgpt


async def parse_menu(image_path: str) -> List[Pizza]:
    # вызывaем метод из openai_client
    raw = await ask_chatgpt(image_path)


    # ожидаем JSON-массив объектов {name: str}
    data = json.loads(raw)
    # конструируем список Pizza
    return [
        Pizza(id=i + 1, name=item.get("name", "").strip())
        for i, item in enumerate(data)
    ]
