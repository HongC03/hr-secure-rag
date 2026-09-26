"""GPT answer provider."""
from backend.services.llm_config import DEFAULT_GPT_BASE_URL, DEFAULT_GPT_MODEL
from backend.services.llm_service import ChatCompletionService


class GptService(ChatCompletionService):
    def __init__(self, *, api_key: str, model: str = DEFAULT_GPT_MODEL, base_url: str = DEFAULT_GPT_BASE_URL) -> None:
        super().__init__(api_key=api_key, model=model, base_url=base_url)
