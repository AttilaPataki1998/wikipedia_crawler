from fastapi import FastAPI
from pydantic import BaseModel

from wikicrawler.analyzer import Analyzer

app = FastAPI()


class Input(BaseModel):
    article: str
    depth: int = 0
    ignore_list: list[str] = []
    percentile: int


@app.get("/word-frequency")
async def get_word_frequency(article: str, depth: int) -> dict[str, list[int, float]] | dict:
    analyzer = Analyzer(article, depth)
    result = await analyzer.analyze()
    return result


@app.post("/keywords")
async def get_specified_word_frequency(inp: Input) -> dict[str, list[int, float]] | dict:
    analyzer = Analyzer(inp.article, inp.depth, inp.ignore_list, inp.percentile)
    result = await analyzer.analyze()
    return result
