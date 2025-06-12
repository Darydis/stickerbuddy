from typing import List
from PIL import Image
import pytesseract

from .models import Pizza


def parse_menu(image_path: str) -> List[Pizza]:
    text = pytesseract.image_to_string(Image.open(image_path), lang='eng+rus')
    pizzas = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if '-' in line:
            name_part, price_part = line.split('-', 1)
        else:
            name_part, price_part = line, ''
        name = name_part.strip()
        price = 0.0
        for token in price_part.split():
            token = token.replace(',', '.').replace('р', '')
            try:
                price = float(token)
                break
            except ValueError:
                continue
        pizzas.append(Pizza(id=len(pizzas) + 1, name=name, price=price))
    return pizzas
