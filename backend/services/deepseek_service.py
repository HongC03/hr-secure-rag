"""DeepSeek answer provider."""
from backend.services.llm_config import DEFAULT_DEEPSEEK_BASE_URL, DEFAULT_DEEPSEEK_MODEL
from backend.services.llm_service import ChatCompletionService


class DeepSeekService(ChatCompletionService):
    def __init__(self, *, api_key: str, model: str = DEFAULT_DEEPSEEK_MODEL, base_url: str = DEFAULT_DEEPSEEK_BASE_URL) -> None:
        super().__init__(api_key=api_key, model=model, base_url=base_url)
