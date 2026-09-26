"""Select an answer provider from server-side configuration."""
import os
from pathlib import Path

from dotenv import load_dotenv

from backend.services.deepseek_service import DeepSeekService
from backend.services.gpt_service import GptService
from backend.services.llm_service import LlmService


def llm_from_environment() -> LlmService | None:
    load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)
    provider = os.environ.get("LLM_PROVIDER", "").strip().lower()
    if not provider:
        return None
    if provider == "gpt":
        return GptService(api_key=os.environ.get("OPENAI_API_KEY", ""))
    if provider == "deepseek":
        return DeepSeekService(api_key=os.environ.get("DEEPSEEK_API_KEY", ""))
    raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")
