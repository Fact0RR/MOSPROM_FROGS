# убрал логирование import logging
from abc import ABC, abstractmethod

class BaseEmbeddingModel(ABC):
    @abstractmethod
    def create_embedding(self, text):
        pass


class OpenAIEmbeddingModel(BaseEmbeddingModel):
    """
    Placeholder retained for legacy imports. The project now relies on external
    embedding services (e.g. SG_Lang) instead of local OpenAI/SBERT wrappers.
    """

    def __init__(self, *args, **kwargs):
        raise RuntimeError(
            "OpenAIEmbeddingModel is no longer available. Provide an embedding model "
            "implementation or rely on the remote embeddings pipeline."
        )

    def create_embedding(self, text):
        raise RuntimeError("OpenAIEmbeddingModel cannot generate embeddings.")
