import wikipediaapi
from textblob import TextBlob
from collections import Counter


class Wikipedia:
    """
        A basic class for fetching information from wikipedia based on the title.
    """

    def __init__(self, article_title: str) -> None:
        self.user_agent = "WordAnalyzer"
        self.wiki = wikipediaapi.Wikipedia(self.user_agent, language="en")
        self.title = article_title
        self.text: str = None
        self.links: list = None
        self._load_page()

    def _load_page(self) -> None:
        page = self.wiki.article(self.title)

        if not page.exists():
            error_msg = f"Could not get page titled {self.title}."
            " Maybe the article you are looking for does not exist."
            print(error_msg)
            return

        self.text = page.text
        self.links = page.links


class Analyzer:
    def __init__(self, article_title: str, depth: int = 0, ignore: list[str] = [], percentile: int = 100) -> None:
        self.title = article_title
        self.depth = depth
        self.ignore_list = ignore,
        self.threshold = percentile
        self.wiki = Wikipedia(self.title)

    async def analyze(self) -> dict[str, int]:
        blob = TextBlob(self.wiki.text) if self.wiki.text else TextBlob("")
        result = Counter(blob.word_counts)
        visited = {self.title}
        current_linked_pages = self.wiki.links or {}

        for _ in range(self.depth):
            next_linked_pages = {}
            for title in current_linked_pages:
                if title in visited:
                    continue

                freqs, links = self.get_data(title)
                result += freqs
                next_linked_pages.update(links)
                visited.add(title)

            current_linked_pages = next_linked_pages

        return dict(result)

    def get_data(self, title: str) -> (Counter, dict):
        wiki = Wikipedia(title)
        blob = TextBlob(wiki.text) if wiki.text else TextBlob("")
        freqs = Counter(blob.word_counts)
        links = wiki.links or {}
        return freqs, links
