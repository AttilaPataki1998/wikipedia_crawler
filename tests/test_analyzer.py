import pytest
import pytest_asyncio
import polars as pl
from collections import Counter
from unittest.mock import MagicMock, patch
from wikicrawler.analyzer import Wikipedia, WikipediaCLient, Analyzer

from fastapi import HTTPException


# -------------------------------
# Mock Wikipedia class for tests
# -------------------------------
class MockWikipediaClient(WikipediaCLient):
    def __init__(self) -> None:
        self.articles = {
            "MockArticle": "This is a test article with some test words.",
            "Python_(programming_language)": "Python is a programming language. Python is great for data science.",
            "Data_science": "Data science is an interdisciplinary field that uses scientific methods, processes, algorithms and systems to extract knowledge and insights from structured and unstructured data.",
            "EmptyArticle": "",
            "OnlyStopWords": "the and is a",
            "NoLinks": "Some text without links."
        }
        self.links = {
            "MockArticle": {"LinkedArticle1": None, "LinkedArticle2": None},
            "Python_(programming_language)": {"OpenAI": None, "Wikipedia": None},
            "Data_science": {"Machine_Learning": None, "Statistics": None},
            "EmptyArticle": {},
            "OnlyStopWords": {},
            "NoLinks": {}
        }

    def get_article_text(self, title: str) -> str:
        return self.articles.get(title, "")
        
    def get_article_links(self, title: str) -> dict:
        return self.links.get(title, {})


@pytest.fixture
def mock_page():
    mock = MagicMock()
    mock.exists.return_value = True
    mock.text = "This is a sample Wikipedia article text."
    mock.links = {
        "Python_(programming_language)": MagicMock(),
        "Talk:Python": MagicMock(),  # This should be filtered out
        "OpenAI": MagicMock()
    }
    return mock


@pytest.fixture
def mock_page_not_found():
    mock = MagicMock()
    mock.exists.return_value = False
    return mock


@patch("wikicrawler.analyzer.wikipediaapi.Wikipedia")
def test_get_article_text_call(mock_wikipedia, mock_page):
    instance = mock_wikipedia.return_value
    instance.article.return_value = mock_page

    client = Wikipedia()
    text = client.get_article_text("Python_(programming_language)")

    mock_wikipedia.assert_called_once_with("WordAnalyzer", language="en")
    instance.article.assert_called_once_with("Python_(programming_language)")
    assert text == mock_page.text


@patch("wikicrawler.analyzer.wikipediaapi.Wikipedia")
def test_get_article_links_call(mock_wikipedia, mock_page):
    instance = mock_wikipedia.return_value
    instance.article.return_value = mock_page

    client = Wikipedia()
    links = client.get_article_links("Python_(programming_language)")

    mock_wikipedia.assert_called_once_with("WordAnalyzer", language="en")
    instance.article.assert_called_once_with("Python_(programming_language)")
    assert "Python_(programming_language)" in links
    assert "Talk:Python" not in links
    assert "OpenAI" in links


@patch("wikicrawler.analyzer.wikipediaapi.Wikipedia")
def test_get_article_text_not_found(mock_wikipedia, mock_page_not_found):
    instance = mock_wikipedia.return_value
    instance.article.return_value = mock_page_not_found

    client = Wikipedia()

    with pytest.raises(HTTPException) as exc_info:
        client.get_article_text("NonExistentPage")
    
    assert "Could not get page titled NonExistentPage" in str(exc_info.value)

@patch("wikicrawler.analyzer.wikipediaapi.Wikipedia")
def test_get_article_links_not_found(mock_wikipedia, mock_page_not_found):
    instance = mock_wikipedia.return_value
    instance.article.return_value = mock_page_not_found

    client = Wikipedia()

    with pytest.raises(HTTPException) as exc_info:
        client.get_article_links("NonExistentPage")
    
    assert "Could not get page titled NonExistentPage" in str(exc_info.value)


def test_get_data_basic():
    mock_wiki = MockWikipediaClient()
    analyzer = Analyzer("MockArticle", mock_wiki, ignore=["the", "is"])
    counts, num_words, links = analyzer.get_data("MockArticle")

    assert isinstance(counts, Counter)
    assert "test" in counts
    assert "the" not in counts  # ignored
    assert num_words == 9
    assert "LinkedArticle1" in links


def test_filter_by_threshold():
    mock_wiki = MockWikipediaClient()
    analyzer = Analyzer("MockArticle", mock_wiki, percentile=50)

    # Simulate a simple DataFrame with counts and percentages
    df = pl.DataFrame({
        "word1": [10, 60],  # 60 > 50 → keep
        "word2": [5, 40],   # 40 < 50 → drop
    })

    result = analyzer.filter_by_threshold(df)

    assert "word1" in result.columns
    assert "word2" not in result.columns


@pytest.mark.asyncio
async def test_analyze_basic():
    mock_wiki = MockWikipediaClient()
    analyzer = Analyzer("MockArticle", mock_wiki, depth=0, ignore=["the", "is"], percentile=0)

    result = await analyzer.analyze()

    assert isinstance(result, dict)
    assert all(isinstance(v, list) and len(v) == 2 for v in result.values())  # each value: [count, freq]
    assert "test" in result


# --------------------------
# Test: Edge Case - Empty Text
# --------------------------
def test_get_data_empty_article():
    mock_wiki = MockWikipediaClient()
    analyzer = Analyzer("EmptyArticle", mock_wiki)
    counts, num_words, links = analyzer.get_data("EmptyArticle")

    assert num_words == 0
    assert counts == Counter()
    assert isinstance(links, dict)


# --------------------------
# Test: Edge Case - Only Stopwords
# --------------------------
def test_get_data_only_stopwords():
    mock_wiki = MockWikipediaClient()
    analyzer = Analyzer("OnlyStopWords", mock_wiki, ignore=["the", "and", "is", "a"])
    counts, num_words, _ = analyzer.get_data("OnlyStopWords")
    assert num_words == 4  # total words before filtering
    assert counts == Counter()  # all words ignored


# --------------------------
# Test: Edge Case - No Links
# --------------------------
@pytest.mark.asyncio
async def test_analyze_no_links():
    mock_wiki = MockWikipediaClient()
    analyzer = Analyzer("NoLinks", mock_wiki)
    result = await analyzer.analyze()
    assert isinstance(result, dict)
    assert len(result) > 0  # should still return word counts
    assert all(isinstance(v, list) and len(v) == 2 for v in result.values())


# --------------------------
# Test: Edge Case - High Threshold
# --------------------------
def test_filter_by_threshold_no_columns_pass():
    mock_wiki = MockWikipediaClient()
    analyzer = Analyzer("MockArticle", mock_wiki, percentile=1000)  # absurdly high threshold

    df = pl.DataFrame({
        "word1": [10, 5],
        "word2": [7, 3],
    })

    result = analyzer.filter_by_threshold(df)

    assert result.shape[1] == 0  # no columns should pass