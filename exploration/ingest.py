import argparse
import logging

from llama_index.core.readers.base import BaseReader
from llama_index.core.schema import Document

from ..git_to_jsonl import yield_feed_items

logger = logging.getLogger(__name__)


class HNSmallSiteFeedRepo(BaseReader):
    def __init__(self, hn_small_sites_feed_repo: str):
        self.hn_small_sites_feed_repo = hn_small_sites_feed_repo

    def lazy_load_data(self):
        for feed_item in yield_feed_items(self.hn_small_sites_feed_repo):
            print(
                f"{feed_item.last_source_commit} {feed_item.guid}: {feed_item.title.strip()}"  # noqa: E501
            )
            body = feed_item.description.split("<!-- hnss:readable-content -->")[1]
            yield Document(
                id_=feed_item.guid,
                text=body,
                metadata={
                    "title": feed_item.title,
                    "link": feed_item.link,
                    "pub_date": feed_item.pub_date,
                    "last_source_commit": feed_item.last_source_commit,
                },
            )


def main():
    parser = argparse.ArgumentParser(
        description="CLI program for HN_SMALL_SITES_FEED_REPO"
    )
    parser.add_argument(
        "HN_SMALL_SITES_FEED_REPO", type=str, help="Path to HN_SMALL_SITES_FEED_REPO"
    )
    args = parser.parse_args()
    hn_small_sites_feed_repo = args.HN_SMALL_SITES_FEED_REPO
    for feed_item in yield_feed_items(hn_small_sites_feed_repo):
        print(
            f"{feed_item.last_source_commit} {feed_item.guid}: {feed_item.title.strip()}"  # noqa: E501
        )


if __name__ == "__main__":
    main()
