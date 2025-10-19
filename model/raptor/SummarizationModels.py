# убрал логирование import logging
import os
from abc import ABC, abstractmethod

# убрал from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_random_exponential
# убрал логирование logging.basicConfig(format="%(asctime)s - %(message)s", level=logging.INFO)


class BaseSummarizationModel(ABC):
    @abstractmethod
    def summarize(self, context, max_tokens=150):
        pass


class GPT3TurboSummarizationModel(BaseSummarizationModel):
    """Placeholder implementation used solely to keep configuration defaults working."""

    def summarize(self, context, max_tokens=150):  # type: ignore[override]
        return context


class GPT3SummarizationModel(BaseSummarizationModel):
    """Historical stub retained for compatibility with upstream imports."""

    def summarize(self, context, max_tokens=150):  # type: ignore[override]
        return context
