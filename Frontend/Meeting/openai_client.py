# openai_client.py

from openai import OpenAI
from .config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def ask_gpt(prompt: str, model: str = "gpt-5") -> str:
    """
    GPT에게 질문하고 응답 텍스트만 반환하는 함수.
    """

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return completion.choices[0].message.content
