# убрал логирование import logging
import os

# убрал  from openai import OpenAI


import getpass
from abc import ABC, abstractmethod

try:
    import torch  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    torch = None
from tenacity import retry, stop_after_attempt, wait_random_exponential
from transformers import T5ForConditionalGeneration, T5Tokenizer


class BaseQAModel(ABC):
    @abstractmethod
    def answer_question(self, context, question):
        pass


#убрал  class GPT3QAModel(BaseQAModel):
# убрал  class GPT3TurboQAModel(BaseQAModel):
# убрал  class GPT4QAModel(BaseQAModel):

class GPT3TurboQAModel(BaseQAModel):
    """Placeholder implementation to satisfy imports; retrieval does not invoke it."""

    def answer_question(self, context, question):  # type: ignore[override]
        return ""


class UnifiedQAModel(BaseQAModel):
    def __init__(self, model_name="allenai/unifiedqa-v2-t5-3b-1363200"):
        if torch is None:
            raise ImportError(
                "UnifiedQAModel requires the optional dependency 'torch'. "
                "Install torch to use this model."
            )
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = T5ForConditionalGeneration.from_pretrained(model_name).to(
            self.device
        )
        self.tokenizer = T5Tokenizer.from_pretrained(model_name)

    def run_model(self, input_string, **generator_args):
        input_ids = self.tokenizer.encode(input_string, return_tensors="pt").to(
            self.device
        )
        res = self.model.generate(input_ids, **generator_args)
        return self.tokenizer.batch_decode(res, skip_special_tokens=True)

    def answer_question(self, context, question):
        input_string = question + " \\n " + context
        output = self.run_model(input_string)
        return output[0]
