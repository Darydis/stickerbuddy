import asyncio
import os

import httpx
import openai

# Prepare OpenAI client with proxy
api_key = os.getenv("OPENAI_API_KEY")
ihttpx = httpx.Client(
    proxies={
        "http://": "http://JuTqmCNApNGz7n:dzera.nat.i@216.107.136.148:42204",
        "https://": "http://JuTqmCNApNGz7n:dzera.nat.i@216.107.136.148:42204",
    },
    trust_env=False
)
openai_client = openai.OpenAI(api_key=api_key, http_client=ihttpx)


# --- OpenAI query ---
async def ask_chatgpt(img_url):
    prompt = (
        "Распознай на изображении меню названия пицц. "
        "Верни JSON-массив объектов {name: str}."
    )
    messages = [
        {"role": "system", "content": prompt},
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": img_url}
                }

            ]
        }
    ]
    resp = await asyncio.to_thread(
        openai_client.chat.completions.create,
        model="gpt-4.1-nano",
        messages=messages,
        max_tokens=150,
        temperature=0,
        top_p=1
    )
    return resp.choices[0].message.content.strip()
