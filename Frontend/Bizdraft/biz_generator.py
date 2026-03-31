# biz_generator.py

from .openai_client import ask_gpt


####### 사업 개요 생성 #######

def generate_titles(keywords: str, prompt_template: str) -> str:
    prompt = prompt_template.format(keywords=keywords)
    return ask_gpt(prompt)


def generate_overview(title: str, prompt_template: str) -> str:
    prompt = prompt_template.format(title=title)
    return ask_gpt(prompt)


def generate_need(title: str, purpose: str, content: str, prompt_template: str) -> str:
    prompt = prompt_template.format(
        title=title,
        purpose=purpose,
        content=content,
    )
    return ask_gpt(prompt)


def generate_suggestion(title: str, purpose: str, content: str, need: str, prompt_template: str) -> str:
    prompt = prompt_template.format(
        title=title,
        purpose=purpose,
        content=content,
        need=need
    )
    return ask_gpt(prompt)


####### 참고 자료 생성 #######

def generate_reference1(title: str, purpose: str, content: str, prompt_template: str) -> str:
    prompt = prompt_template.format(
        title=title,
        purpose=purpose,
        content=content
    )
    return ask_gpt(prompt)


def generate_reference2(title: str, purpose: str, content: str, need: str, prompt_template: str, context_data: str = "") -> str:
    prompt = prompt_template.format(
        title=title,
        purpose=purpose,
        content=content,
        need=need,
        context_data=context_data
    )
    return ask_gpt(prompt)


def generate_reference3(title: str, purpose: str, content: str, need: str, prompt_template: str, context_data: str = "") -> str:
    prompt = prompt_template.format(
        title=title,
        purpose=purpose,
        content=content,
        need=need,
        context_data=context_data
    )
    return ask_gpt(prompt)


def generate_reference4(title: str, purpose: str, content: str, need: str, prompt_template: str, context_data: str = "") -> str:
    prompt = prompt_template.format(
        title=title,
        purpose=purpose,
        content=content,
        need=need,
        context_data=context_data
    )
    return ask_gpt(prompt)

def summarize_business_evidences(evidences: list[str], max_len: int = 40) -> list[str]:
    """
    사업근거 문장 리스트를 받아
    각 문장을 max_len자 이내로 요약하여 반환
    (OpenAI 호출 1회, 토큰 최소화)
    """

    if not evidences:
        return []

    # 이미 짧은 문장은 그대로 사용
    short = []
    long = []

    for e in evidences:
        if len(e) <= max_len:
            short.append(e)
        else:
            long.append(e)

    if not long:
        return evidences

    # 번호 유지해서 한 번에 요청
    joined = "\n".join(
        [f"{i+1}. {e}" for i, e in enumerate(long)]
    )

    prompt = (
        "아래 문장들을 각각 40~50자 이내로 핵심만 요약하라\n"
        "의미는 유지하고 불필요한 수식어는 제거하라\n"
        "출력은 같은 번호를 유지하라\n\n"
        f"{joined}"
    )

    result = ask_gpt(prompt)

    # 결과 파싱
    summarized = []
    for line in result.splitlines():
        if "." in line:
            summarized.append(line.split(".", 1)[1].strip())

    # 원래 순서 복원
    final = []
    long_idx = 0
    for e in evidences:
        if len(e) <= max_len:
            final.append(e)
        else:
            final.append(summarized[long_idx])
            long_idx += 1

    return final
