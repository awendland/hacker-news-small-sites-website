from datetime import datetime
from email.utils import parsedate_to_datetime
from functools import lru_cache

import feedparser
from cachetools import TTLCache, cached
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from chroma_query import QueryEngine
from git_to_jsonl import FeedItem, process_feed_item

app = FastAPI()

templates = Jinja2Templates(directory="web-templates")

query_engine = QueryEngine(data_db="data.db")


@lru_cache
def cached_query(query: str):
    return list(query_engine.query(query, num_results=80))


@cached(TTLCache(1, ttl=3600))
def cached_feed():
    feed = feedparser.parse(
        "https://raw.githubusercontent.com/awendland/hacker-news-small-sites/generated/feeds/hn-small-sites-score-1.xml"
    )
    return [
        process_feed_item(
            FeedItem(
                guid=e.guid,
                title=e.title,
                link=e.link,
                pub_date=parsedate_to_datetime(e.published),
                description=e.summary,
                last_source_commit=None,
            )
        )
        for e in feed.entries
    ]


@app.get("/", response_class=HTMLResponse)
async def read_item(request: Request, query: str | None = None):
    start = datetime.now()
    if query:
        query_results = cached_query(query)
        results = (
            {"doc": doc, "distances": [s["distance"] for s in search_info]}
            for doc, search_info in query_results
        )
        feed = None
    else:
        feed = cached_feed()
        results = None
    return templates.TemplateResponse(
        request=request,
        name="search.html",
        context={
            "query": query,
            "results": results,
            "feed": feed,
            "load_time": datetime.now() - start,
        },
    )
