
from typing import Literal
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    top_k: Literal[5, 10, 20] = 5
    language: Literal["all", "en", "ta"] = "all"
    max_distance: float | None = Field(
        default=None, ge=0
    )


class SearchResult(BaseModel):
    document_id: str
    title: str
    content: str
    source_url: str | None = None
    page: int | None = None
    language: str | None = None
    modality: str | None = None
    distance: float
    score_type: str = "squared_l2_distance"


class SearchResponse(BaseModel):
    query: str
    total_results: int
    execution_time_ms: float
    results: list[SearchResult]
