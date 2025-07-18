import asyncio
from collections import Counter
import polars as pl
from textblob import TextBlob
import wikipediaapi


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
        self.links = {title: wiki_obj for title, wiki_obj in page.links.items() if "Talk:" not in title}


class Analyzer:
    def __init__(self, article_title: str, depth: int = 0, ignore: list[str] = [], percentile: int = 100) -> None:
        self.title = article_title
        self.depth = depth
        self.ignore_list = set(ignore)
        self.threshold = percentile

    async def analyze(self) -> dict[str, list[float, float]]:
        visited = {self.title}
        result_counter, total_num_words, current_linked_pages = self.get_data(self.title)

        for _ in range(self.depth):
            next_linked_pages = {}
            for title in current_linked_pages:
                if title in visited:
                    continue

                counts, num_words, links = self.get_data(title)
                result_counter += counts
                next_linked_pages.update(links)
                total_num_words += num_words
                visited.add(title)

            current_linked_pages = next_linked_pages

        counter_df = pl.DataFrame(result_counter)
        freq_df = counter_df.select(
            pl.col("*") * 100 / total_num_words
        )

        result = pl.concat([counter_df, freq_df], how="vertical_relaxed")

        result = self.filter_by_percentile(result)

        print(">>>>>>>>>>>>>>>>>>>>>>>>")
        print(result)
        print(">>>>>>>>>>>>>>>>>>>>>>>>")

        return dict(result_counter)

    def get_data(self, title: str) -> (Counter, int, dict):
        wiki = Wikipedia(title)
        blob = TextBlob(wiki.text) if wiki.text else TextBlob("")
        filtered_count = {
            word: count for word, count in blob.word_counts.items() if word not in self.ignore_list
        }

        counts = Counter(filtered_count)
        links = wiki.links or {}
        num_words = len(blob.words)

        return counts, num_words, links

    # FIXME: Finish filtering later
    def filter_by_percentile(self, df: pl.DataFrame) -> None:
        return filtered_df


a = Analyzer("Seabrooke", 0, ["seabrooke"], 5)


async def get_res():
    res = await a.analyze()
    print(res)

asyncio.get_event_loop().run_until_complete(get_res())
