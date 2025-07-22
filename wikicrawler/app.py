from fastapi import FastAPI, Request
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
from typing import Dict, List

from wikicrawler.analyzer import Analyzer, Wikipedia

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except RateLimitExceeded:
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded, please try again later."},
        )


# Pydantic payload for POST endpoint
class Payload(BaseModel):
    article: str = Field(..., min_length=1)
    depth: int = Field(..., ge=0)
    ignore_list: List[str] = []
    percentile: int = Field(ge=0, le=100)


@app.get("/word-frequency")
@limiter.limit("30/minute")
async def get_word_frequency(request: Request, article: str, depth: int) -> Dict[str, List[float]] | dict:
    wiki_client = Wikipedia()
    analyzer = Analyzer(article, wiki_client, depth)
    result = await analyzer.analyze()
    return result


@app.post("/keywords")
@limiter.limit("15/minute")
async def filter_keywords(request: Request, payload: Payload) -> Dict[str, List[float]] | dict:
    wiki_client = Wikipedia()
    analyzer = Analyzer(payload.article, wiki_client, payload.depth, payload.ignore_list, payload.percentile)
    result = await analyzer.analyze()
    return result
