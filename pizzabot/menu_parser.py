from typing import List
import os
import json
import base64
import openai

from .models import Pizza


def parse_menu(image_path: str) -> List[Pizza]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    client = openai.OpenAI(api_key=api_key)

    with open(image_path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode("utf-8")

    prompt = (
        "Распознай на изображении меню названия пицц и их цены в рублях. "
        "Верни JSON-массив объектов {name: str, price: float}. Цена может быть 0, если не указана."
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"},
                    },
                ],
            }
        ],
        max_tokens=300,
    )

    text = response.choices[0].message.content
    data = json.loads(text)

    pizzas = [
        Pizza(id=i + 1, name=item.get("name", "").strip(), price=float(item.get("price", 0)))
        for i, item in enumerate(data)
    ]
    return pizzas
