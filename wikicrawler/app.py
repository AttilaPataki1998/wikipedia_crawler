from fastapi import FastAPI
from pydantic import BaseModel, Field

from wikicrawler.analyzer import Analyzer, Wikipedia

app = FastAPI()


class Payload(BaseModel):
    article: str = Field(..., min_length=1)
    depth: int = Field(..., ge=0)
    ignore_list: list[str] = []
    percentile: int = Field(ge=0, le=100)


@app.get("/word-frequency")
async def get_word_frequency(article: str, depth: int) -> dict[str, list[int, float]] | dict:
    wiki_client = Wikipedia()
    analyzer = Analyzer(article, wiki_client, depth)
    result = await analyzer.analyze()
    return result


@app.post("/keywords")
async def get_specified_word_frequency(payload: Payload) -> dict[str, list[int, float]] | dict:
    wiki_client = Wikipedia()
    analyzer = Analyzer(payload.article, wiki_client, payload.depth, payload.ignore_list, payload.percentile)
    result = await analyzer.analyze()
    return result
