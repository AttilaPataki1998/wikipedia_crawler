import pytest
import pytest_asyncio
import polars as pl
from collections import Counter
from unittest.mock import MagicMock, patch
from wikicrawler.analyzer import Wikipedia, Analyzer


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


@patch("wikicrawler.analyzer.wikipediaapi.Wikipedia")
def test_load_valid_page(mock_wikipedia, mock_page):
    # Setup the mock
    instance = mock_wikipedia.return_value
    instance.article.return_value = mock_page

    wiki = Wikipedia("Python")

    assert wiki.text == "This is a sample Wikipedia article text."
    assert isinstance(wiki.links, dict)
    assert "Python_(programming_language)" in wiki.links
    assert "OpenAI" in wiki.links
    assert "Talk:Python" not in wiki.links  # should be filtered out


@patch("wikicrawler.analyzer.wikipediaapi.Wikipedia")
def test_load_nonexistent_page(mock_wikipedia):
    # Setup a mock page that doesn't exist
    mock_page = MagicMock()
    mock_page.exists.return_value = False

    instance = mock_wikipedia.return_value
    instance.article.return_value = mock_page

    wiki = Wikipedia("NonExistentPage123456")

    assert wiki.text is None
    assert wiki.links is None


# --- Mock Wikipedia class ---
class MockWikipedia:
    def __init__(self, title):
        self.title = title
        self.text = "This is a test. Testing the test method and test behavior."
        # self.links = {
        #     "LinkedArticle1": None,
        #     "LinkedArticle2": None
        # }
        self.links = None

# --- Patch the real Wikipedia class ---
@pytest.fixture
def patch_wikipedia(monkeypatch):
    monkeypatch.setattr("wikicrawler.analyzer.Wikipedia", MockWikipedia)


# --- Test get_data ---
def test_get_data_basic(patch_wikipedia):
    analyzer = Analyzer("MockArticle", ignore=["the", "a"])
    counts, num_words, links = analyzer.get_data("MockArticle")

    assert isinstance(counts, Counter)
    assert "test" in counts
    assert "the" not in counts  # ignored
    assert num_words == 11
    #assert "LinkedArticle1" in links


# --- Test filter_by_threshold ---
def test_filter_by_threshold():
    analyzer = Analyzer("MockArticle", percentile=50)

    # Simulate a simple DataFrame with counts and percentages
    df = pl.DataFrame({
        "word1": [10, 60],  # 60 > 50 → keep
        "word2": [5, 40],   # 40 < 50 → drop
    })

    result = analyzer.filter_by_threshold(df)

    assert "word1" in result.columns
    assert "word2" not in result.columns


@pytest.mark.asyncio
async def test_analyze_basic(patch_wikipedia):
    analyzer = Analyzer("MockArticle", depth=0, ignore=["is", "the"], percentile=0)

    result = await analyzer.analyze()

    assert isinstance(result, dict)
    assert all(isinstance(v, list) and len(v) == 2 for v in result.values())  # each value: [count, freq]
    assert "test" in result


# -------------------------------
# Mock Wikipedia class for tests
# -------------------------------
class MockWikipedia2:
    def __init__(self, title):
        self.title = title
        self.text = {
            "EmptyArticle": "",
            "OnlyStopWords": "the and is a",
            "NoLinks": "Some text without links.",
        }.get(title, "This is a test. Testing words and frequency.")
        
        if title == "NoLinks":
            self.links = None
        else:
            self.links = {
                "LinkedArticle1": None,
                "LinkedArticle2": None
            }


# ----------------------------
# Automatically patch Wikipedia
# ----------------------------
@pytest.fixture
def patch_wikipedia_edge(monkeypatch):
    monkeypatch.setattr("wikicrawler.analyzer.Wikipedia", MockWikipedia2)


# --------------------------
# Test: Edge Case - Empty Text
# --------------------------
def test_get_data_empty_article(patch_wikipedia_edge):
    analyzer = Analyzer("EmptyArticle")
    counts, num_words, links = analyzer.get_data("EmptyArticle")

    assert num_words == 0
    assert counts == Counter()
    assert isinstance(links, dict)


# --------------------------
# Test: Edge Case - Only Stopwords
# --------------------------
def test_get_data_only_stopwords(patch_wikipedia_edge):
    analyzer = Analyzer("OnlyStopWords", ignore=["the", "and", "is", "a"])
    counts, num_words, _ = analyzer.get_data("OnlyStopWords")
    assert num_words == 4  # total words before filtering
    assert counts == Counter()  # all words ignored


# --------------------------
# Test: Edge Case - No Links
# --------------------------
@pytest.mark.asyncio
async def test_analyze_no_links(patch_wikipedia_edge):
    analyzer = Analyzer("NoLinks")
    result = await analyzer.analyze()
    assert isinstance(result, dict)
    assert len(result) > 0  # should still return word counts
    assert all(isinstance(v, list) and len(v) == 2 for v in result.values())


# --------------------------
# Test: Edge Case - High Threshold
# --------------------------
def test_filter_by_threshold_no_columns_pass():
    analyzer = Analyzer("MockArticle", percentile=1000)  # absurdly high threshold

    df = pl.DataFrame({
        "word1": [10, 5],
        "word2": [7, 3],
    })

    result = analyzer.filter_by_threshold(df)

    assert result.shape[1] == 0  # no columns should pass