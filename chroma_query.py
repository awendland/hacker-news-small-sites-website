import argparse
import json
import sqlite3
from collections import defaultdict
from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Annotated, Generator, List, Tuple, TypedDict

import chromadb
from pydantic import BaseModel, BeforeValidator

from embedding_models import get_embedder


class QueryResultMetadata(TypedDict):
    embedding_id: str
    distance: float


# Example:
# {
#   "guid": "hacker-news-small-sites-39500135",
#   "num_score": 2,
#   "num_comments": 1,
#   "thread_link": "https://news.ycombinator.com/item?id=39500135",
#   "pub_date": "Sun, 25 Feb 2024 12:08:42 GMT",
#   "last_source_commit": "43f356317f9ab30dad07058f3bc71fea78213c64",
#   "title": "Giving Ada a Chance (2021)",
#   "link": "https://ajxs.me/blog/Giving_Ada_a_Chance.html",
#   "text": "<div id=\"readability-page-1\" class=\"page\"><div>\n\t\t<p><span>TL;DR:</span>\n\tAda is an extremely interesting and..." # noqa: E501
# }
class HNSSEntry(BaseModel):
    guid: str
    num_score: int
    num_comments: int
    thread_link: str
    pub_date: Annotated[datetime, BeforeValidator(parsedate_to_datetime)]
    title: str
    link: str
    text: str
    last_source_commit: str | None


class QueryEngine:
    def __init__(self, data_db: str, chroma_dir: str):
        self.vector_client = chromadb.PersistentClient(path=chroma_dir)
        self.vector_collection = self.vector_client.get_collection(
            name="hn_small_sites"
        )
        self.db_client = sqlite3.connect(data_db)
        self.embedder, self.embedder_name = get_embedder()

    def query(
        self, query: str, num_results: int = 10
    ) -> Generator[Tuple[HNSSEntry, List[QueryResultMetadata]], None, None]:
        query_embeddings = self.embedder.embed_query(query)
        results = self.vector_collection.query(query_embeddings, n_results=num_results)
        doc_results = defaultdict[str, List[QueryResultMetadata]](list)
        ids = results["ids"][0]
        distances = results["distances"][0] if results["distances"] else []
        for id, ds in zip(ids, distances):
            hnss_id = id.split(":")[0]
            doc_results[hnss_id].append({"embedding_id": id, "distance": ds})
        for id, sr in doc_results.items():
            cursor = self.db_client.execute(
                """
                SELECT id, content FROM documents WHERE id = ?
            """,
                (id,),
            )
            row = cursor.fetchone()
            if row:
                yield HNSSEntry.model_validate_json(row[1]), sr

    def count_documents(self) -> int:
        return self.db_client.execute("SELECT COUNT(*) FROM documents").fetchone()[0]

    def count_embeddings(self) -> int:
        return self.vector_collection.count()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("data_db", help="Path to the data.db file")
    parser.add_argument("query", help="Query to embed and search for in the DB")
    args = parser.parse_args()

    for h, _ in QueryEngine(args.data_db, "./chroma").query(args.query):
        doc = h.model_dump()
        doc.pop("text")
        print(json.dumps(doc, indent=2))
