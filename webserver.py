import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime
from email.utils import parsedate_to_datetime
from functools import lru_cache
from typing import cast

import feedparser
from cachetools import TTLCache, cached
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from chroma_query import QueryEngine
from git_to_jsonl import FeedItem, process_feed_item

templates = Jinja2Templates(directory="web-templates")

query_engine = QueryEngine(
    data_db=os.getenv("HNSS_DATA_DB", "data.db"),
    chroma_dir=os.getenv("HNSS_CHROMA_DIR", "./chroma"),
)


@lru_cache
def cached_query(query: str):
    return list(query_engine.query(query, num_results=80))


@cached(TTLCache(1, ttl=3600))
def cached_doc_count():
    return query_engine.count_documents()


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
                last_source_commit=cast(str, None),
            )
        )
        for e in feed.entries
    ]


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    async def cache_refresher():
        try:
            while True:
                cached_feed()
                await asyncio.sleep(1 * 60)
        except asyncio.CancelledError:
            pass

    task = asyncio.create_task(cache_refresher())
    yield
    task.cancel()
    await task


app = FastAPI(lifespan=app_lifespan)


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
            "doc_count": cached_doc_count(),
            "load_time": datetime.now() - start,
        },
    )
