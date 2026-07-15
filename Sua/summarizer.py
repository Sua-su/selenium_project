"""
로컬 LLM 요약 모듈
llama-cpp-python으로 GGUF 모델을 로드해 기사 본문을 요약합니다.
"""

import os
import threading
from typing import Optional

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "qwen2.5-3b-instruct-q4_k_m.gguf")
MAX_CONTENT_CHARS = 4000  # 모델 컨텍스트 한도 내로 자르기

_lock = threading.Lock()
_llm = None
_load_failed = False


def _get_llm():
    """모델을 최초 1회만 로드하는 지연 싱글톤"""
    global _llm, _load_failed

    if _llm is not None or _load_failed:
        return _llm

    with _lock:
        if _llm is not None or _load_failed:
            return _llm

        if not os.path.exists(MODEL_PATH):
            print(f"요약 모델 파일을 찾을 수 없습니다: {MODEL_PATH}")
            _load_failed = True
            return None

        try:
            from llama_cpp import Llama
            _llm = Llama(
                model_path=MODEL_PATH,
                n_ctx=4096,
                n_threads=max(1, (os.cpu_count() or 4) - 1),
                verbose=False,
            )
        except Exception as e:
            print(f"요약 모델 로딩 실패: {str(e)}")
            _load_failed = True

    return _llm


def is_available() -> bool:
    """요약 기능 사용 가능 여부"""
    return _get_llm() is not None


def summarize(title: str, content: str, sentences: int = 3) -> Optional[str]:
    """기사 제목/본문을 받아 로컬 LLM으로 요약 생성

    Args:
        title: 기사 제목
        content: 기사 본문
        sentences: 목표 요약 문장 수

    Returns:
        요약 텍스트, 실패 시 None
    """
    if not content or not content.strip():
        return None

    llm = _get_llm()
    if llm is None:
        return None

    text = content.strip()
    if len(text) > MAX_CONTENT_CHARS:
        text = text[:MAX_CONTENT_CHARS]

    messages = [
        {
            "role": "system",
            "content": "너는 뉴스 기사를 간결하고 정확하게 요약하는 어시스턴트야. 과장이나 추측 없이 기사에 있는 사실만 요약해.",
        },
        {
            "role": "user",
            "content": (
                f"다음 뉴스 기사를 한국어로 {sentences}문장 이내로 요약해줘. "
                "핵심 사실 위주로 작성하고 요약 외의 다른 말은 하지 마.\n\n"
                f"제목: {title or ''}\n"
                f"본문: {text}"
            ),
        },
    ]

    # llama.cpp 컨텍스트는 동시 호출에 안전하지 않으므로 직렬화
    with _lock:
        try:
            result = llm.create_chat_completion(
                messages=messages,
                max_tokens=300,
                temperature=0.3,
            )
            summary = result["choices"][0]["message"]["content"].strip()
            return summary or None
        except Exception as e:
            print(f"요약 생성 오류: {str(e)}")
            return None
