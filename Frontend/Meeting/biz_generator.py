# biz_generator.py

from openai_client import ask_gpt
from prompt_templates import (
    TITLE_GENERATION_PROMPT,
    OVERVIEW_PROMPT,
    NEED_PROMPT,
    SUGGESTION_PROMPT
)


def generate_titles(keywords: str) -> str:
    prompt = TITLE_GENERATION_PROMPT.format(keywords=keywords)
    return ask_gpt(prompt)


def generate_overview(title: str) -> str:
    prompt = OVERVIEW_PROMPT.format(title=title)
    return ask_gpt(prompt)


def generate_need(title: str, purpose: str, content: str) -> str:
    prompt = NEED_PROMPT.format(
        title=title,
        purpose=purpose,
        content=content
    )
    return ask_gpt(prompt)


def generate_suggestion(title: str, overview: str, need: str) -> str:
    prompt = SUGGESTION_PROMPT.format(
        title=title,
        overview=overview,
        need=need
    )
    return ask_gpt(prompt)
