
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request

from backend.config import EMBEDDING_MODEL
from backend.schemas import (
    SearchRequest,
    SearchResponse,
)
from backend.services.faiss_service import FaissService


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    service = FaissService()

    try:
        service.load()
    except Exception:
        logger.exception("FAISS startup failure")

    app.state.search_service = service
    yield


app = FastAPI(
    title="Tamil Nadu Agriculture Scheme Search API",
    version="1.0.0",
    lifespan=lifespan,
)


def get_service(request: Request) -> FaissService:
    return request.app.state.search_service


@app.get("/api/v1/health")
def health(request: Request):
    service = get_service(request)

    return {
        "status": "healthy" if service.ready else "degraded",
        "vector_db": "connected" if service.ready else "unavailable",
        "embedding_model": EMBEDDING_MODEL,
        "indexed_vectors": service.count,
    }


@app.get("/api/v1/stats")
def stats(request: Request):
    service = get_service(request)

    return {
        "index_ready": service.ready,
        "indexed_vectors": service.count,
        "unique_documents": None,
        "note": (
            "Unique document count requires reliable "
            "document identifiers in metadata."
        ),
    }


@app.post(
    "/api/v1/search",
    response_model=SearchResponse,
)
def search(payload: SearchRequest, request: Request):
    if not payload.query.strip():
        raise HTTPException(
            status_code=422,
            detail="Query cannot be blank",
        )

    service = get_service(request)

    if not service.ready:
        raise HTTPException(
            status_code=503,
            detail="Vector database is not ready",
        )

    start = time.perf_counter()

    try:
        results = service.search(
            query=payload.query.strip(),
            top_k=payload.top_k,
            language=payload.language,
            max_distance=payload.max_distance,
        )
    except Exception:
        logger.exception("Semantic search failed")
        raise HTTPException(
            status_code=500,
            detail="Search operation failed",
        )

    elapsed = (
        time.perf_counter() - start
    ) * 1000

    return SearchResponse(
        query=payload.query,
        total_results=len(results),
        execution_time_ms=round(elapsed, 2),
        results=results,
    )
@app.get("/api/v1/diagnostics")
def diagnostics(request: Request):
    service = get_service(request)

    return {
        "index_ready": service.ready,
        "indexed_vectors": service.count,
        "error": service.error,
    }