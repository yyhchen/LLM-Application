from pydantic import BaseModel
from typing import Any, Dict, List, Optional, Union, Iterable, Tuple, Set, Sequence
import requests

class BGEEmbeddings(BaseModel):
    """Custom embedding model integration using your own API."""

    model: str = "bge-m3"
    base_url: str = "http://localhost:8200/v1/embeddings"
    embedding_ctx_length: int = 8191
    """The maximum number of tokens to embed at once."""
    chunk_size: int = 1000
    """Maximum number of texts to embed in each batch."""
    skip_empty: bool = False
    """Whether to skip empty strings when embedding or raise an error. Defaults to not skipping."""

    def _invocation_params(self) -> Dict[str, Any]:
        return {"model": self.model}

    def _tokenize(self, texts: List[str], chunk_size: int) -> Tuple[Iterable[int], List[str], List[int]]:
        tokens: List[str] = []
        indices: List[int] = []

        for i, text in enumerate(texts):
            # Simple tokenization based on the max length, adjust according to your API's requirements
            for j in range(0, len(text), self.embedding_ctx_length):
                tokens.append(text[j:j + self.embedding_ctx_length])
                indices.append(i)

        return range(0, len(tokens), chunk_size), tokens, indices

    def _get_len_safe_embeddings(self, texts: List[str]) -> List[List[float]]:
        _iter, tokens, indices = self._tokenize(texts, self.chunk_size)
        batched_embeddings: List[List[float]] = []

        for i in _iter:
            response = requests.post(
                self.base_url,
                json={"input": tokens[i:i + self.chunk_size], **self._invocation_params()},
                headers={"Content-Type": "application/json"}
            )
            response_data = response.json() # 这里是一个dict
            embeddings = [item["embedding"] for item in response_data["data"]]
            batched_embeddings.extend(embeddings)

        embeddings = self._process_batched_chunked_embeddings(len(texts), tokens, batched_embeddings, indices)
        return embeddings

    def _process_batched_chunked_embeddings(self, original_text_count: int, tokens: List[str],
                                            batched_embeddings: List[List[float]], indices: List[int]) -> List[List[float]]:
        embeddings = [None] * original_text_count

        for i, embedding in enumerate(batched_embeddings):
            idx = indices[i]
            if embeddings[idx] is None:
                embeddings[idx] = embedding
            else:
                # Here you can decide how to combine embeddings if texts are split
                embeddings[idx] = [sum(x) for x in zip(embeddings[idx], embedding)]

        return embeddings

    def embed_query(self, text: str) -> List[float]:
        return self._get_len_safe_embeddings([text])[0]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._get_len_safe_embeddings(texts)
