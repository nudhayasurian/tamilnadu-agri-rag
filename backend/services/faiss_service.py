
import hashlib
from urllib.parse import urlparse

import faiss
from langchain_community.vectorstores import FAISS

from backend.config import (
    INDEX_PATH,
    EMBEDDING_MODEL,
    TRUST_LOCAL_INDEX,
    EMBEDDING_CONFIG_VERIFIED,
)
from src.embeddings import get_embeddings


def valid_http_url(value):
    if not isinstance(value, str):
        return None
    parsed = urlparse(value)
    if parsed.scheme in ("http", "https") and parsed.netloc:
        return value
    return None


class FaissService:
    def __init__(self):
        self.store = None
        self.error = None

    def load(self):
        self.store = None
        self.error = None

        if not (INDEX_PATH / "index.faiss").is_file():
            self.error = "LangChain FAISS index not found"
            return

        if not (INDEX_PATH / "index.pkl").is_file():
            self.error = "FAISS document store not found"
            return

        if not TRUST_LOCAL_INDEX:
            self.error = "Local index trust not confirmed"
            return

        if not EMBEDDING_CONFIG_VERIFIED:
            self.error = "Embedding configuration not verified"
            return

        try:
            embeddings = get_embeddings()
            store = FAISS.load_local(
                str(INDEX_PATH),
                embeddings,
                allow_dangerous_deserialization=True,
            )

            # Original prototype uses a flat L2 index.
            if store.index.metric_type != faiss.METRIC_L2:
                raise ValueError(
                    "Expected L2 FAISS index"
                )

            vector = embeddings.embed_query(
                "agriculture subsidy"
            )

            if len(vector) != store.index.d:
                raise ValueError(
                    "Embedding dimension mismatch"
                )

            self.store = store

        except Exception:
            self.error = "Index initialization failed"
            raise

    @property
    def ready(self):
        return self.store is not None

    @property
    def count(self):
        if not self.ready:
            return 0
        return int(self.store.index.ntotal)

    def search(self, query, top_k, language, max_distance):
        if not self.ready:
            raise RuntimeError("Index unavailable")

        filters = None
        '''if language != "all":
            filters = {"language": language}
        '''
        results = self.store.similarity_search_with_score(
            query,
            k=top_k,
            fetch_k=max(50, top_k * 10),
            filter=filters,
        )

        output = []

        for doc, distance in results:
            distance = float(distance)

            if (
                max_distance is not None
                and distance > max_distance
            ):
                continue

            metadata = doc.metadata
            source = metadata.get("source", "")
            source_url = valid_http_url(
                metadata.get("source_url")
            ) or valid_http_url(source)

            document_id = metadata.get("document_id")

            if document_id is None:
                document_id = hashlib.sha256(
                    str(source).encode("utf-8")
                ).hexdigest()[:24]

            output.append({
                "document_id": str(document_id),
                "title": str(
                    metadata.get("title")
                    or str(source).replace("\\", "/").split("/")[-1]
                    or "Untitled document"
                ),
                "content": doc.page_content,
                "source_url": source_url,
                "page": metadata.get("page"),
                "language": metadata.get("language"),
                "modality": metadata.get("modality", "pdf"),
                "distance": distance,
                "score_type": "squared_l2_distance",
            })

        return output
