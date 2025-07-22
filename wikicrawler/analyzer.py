from fastapi import HTTPException
from collections import Counter
import polars as pl
from textblob import TextBlob
from typing import Dict, List, Tuple
import wikipediaapi


class WikipediaClient:
    def get_article_text(self, title: str) -> str:
        raise NotImplementedError("This method should be implemented by subclasses.")

    def get_article_links(self, title: str) -> dict:
        raise NotImplementedError("This method should be implemented by subclasses.")


class Wikipedia(WikipediaClient):
    def __init__(self) -> None:
        self.user_agent = "WordAnalyzer"
        self.wiki = wikipediaapi.Wikipedia(self.user_agent, language="en")

    def get_article_text(self, title: str) -> str:
        page = self.wiki.article(title)
        if not page.exists():
            error_msg = f"Could not get page titled {title}. Maybe the article you are looking for does not exist."
            raise HTTPException(status_code=404, detail=error_msg)
        return page.text

    def get_article_links(self, title: str) -> dict:
        page = self.wiki.article(title)
        if not page.exists():
            error_msg = f"Could not get page titled {title}. Maybe the article you are looking for does not exist."
            raise HTTPException(status_code=404, detail=error_msg)
        return {title: linked_page for title, linked_page in page.links.items() if "Talk:" not in title}


class Analyzer:
    def __init__(self, article_title: str, wiki_client: Wikipedia, depth: int = 0, ignore: List[str] = [], percentile: int = 0) -> None:
        self.title = article_title
        self.wiki_client = wiki_client
        self.depth = depth
        self.ignore_list = set(ignore)
        self.threshold = percentile

    async def analyze(self) -> Dict[str, List[float]]:
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

        result = self.filter_by_threshold(result)

        return result.to_dict(as_series=False)

    def get_data(self, title: str) -> Tuple[Counter, int, dict]:
        text = self.wiki_client.get_article_text(title)
        links = self.wiki_client.get_article_links(title)
        blob = TextBlob(text)
        counts = Counter({
            word: count for word, count in blob.word_counts.items() if word not in self.ignore_list
        })
        num_words = len(blob.words)

        return counts, num_words, links

    def filter_by_threshold(self, df: pl.DataFrame) -> pl.DataFrame:
        filtered_cols = [
            col for col in df.columns if df[col][1] > self.threshold
        ]
        filtered_df = df.select(filtered_cols)
        return filtered_df
