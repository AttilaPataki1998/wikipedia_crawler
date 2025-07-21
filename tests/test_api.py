import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock

from wikicrawler.app import app


@pytest.mark.asyncio
@patch("wikicrawler.app.Analyzer.analyze", new_callable=AsyncMock)
async def test_get_word_frequency_success(mock_analyze):
    mock_analyze.return_value = {"python": [10, 5.0], "code": [8, 4.0]}

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/word-frequency", params={"article": "Python", "depth": 1})

    assert response.status_code == 200
    assert "python" in response.json()


@pytest.mark.asyncio
@patch("wikicrawler.app.Analyzer.analyze", new_callable=AsyncMock)
async def test_post_keywords_success(mock_analyze):
    mock_analyze.return_value = {"data": [5, 2.5], "science": [7, 3.5]}

    payload = {
        "article": "Data_science",
        "depth": 2,
        "ignore_list": ["the", "is"],
        "percentile": 1
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/keywords", json=payload)

    assert response.status_code == 200
    assert "data" in response.json()


@pytest.mark.asyncio
async def test_get_missing_params():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/word-frequency", params={"article": "TestOnly"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_post_invalid_payload_type():
    payload = {
        "article": "Data_science",
        "depth": "deep",  # Should be int
        "ignore_list": ["the"],
        "percentile": 10
    }
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/keywords", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
@patch("wikicrawler.app.Analyzer.analyze", new_callable=AsyncMock)
async def test_article_not_found(mock_analyze):
    mock_analyze.return_value = {}
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/word-frequency", params={"article": "FakeTitle123", "depth": 1})
    assert response.status_code == 200
    assert response.json() == {}


@pytest.mark.asyncio
@patch("wikicrawler.app.Analyzer.analyze", new_callable=AsyncMock)
async def test_all_words_filtered_by_percentile(mock_analyze):
    mock_analyze.return_value = {}
    payload = {
        "article": "Machine_learning",
        "depth": 0,
        "ignore_list": [],
        "percentile": 99
    }
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/keywords", json=payload)
    assert response.status_code == 200
    assert response.json() == {}


@pytest.mark.asyncio
@patch("wikicrawler.app.Analyzer.analyze", new_callable=AsyncMock)
async def test_empty_article_title(mock_analyze):
    mock_analyze.return_value = {}
    payload = {
        "article": "",
        "depth": 1,
        "ignore_list": [],
        "percentile": 0
    }
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/keywords", json=payload)
    assert response.status_code in {200, 422}
