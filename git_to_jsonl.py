import argparse
import json
import logging
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from typing import Generator

from lxml import etree

logger = logging.getLogger(__name__)


@dataclass
class FeedItem:
    guid: str
    title: str
    description: str
    link: str
    pub_date: str
    last_source_commit: str


@dataclass
class HNEntry:
    guid: str
    num_score: int | None
    num_comments: int | None
    thread_link: str
    pub_date: str
    last_source_commit: str
    title: str
    link: str
    text: str


def yield_feed_items(
    hn_small_sites_feed_repo: str, until_commit: str = None
) -> Generator[FeedItem, None, None]:
    git_command = ["git", "rev-list", "generated"]
    res_generated_commits = subprocess.run(
        git_command, capture_output=True, text=True, cwd=hn_small_sites_feed_repo
    )
    if res_generated_commits.returncode != 0:
        logger.error(res_generated_commits.stderr)
        return
    generated_commits = res_generated_commits.stdout.strip().split("\n")
    if until_commit:
        try:
            continue_after_commit_index = generated_commits.index(until_commit)
            generated_commits = generated_commits[: continue_after_commit_index - 1]
        except ValueError:
            logger.error(f"Commit {until_commit} not found in the list of commits")
            return
    prev_guids = set()
    for commit in generated_commits:
        try:
            res_git_show = subprocess.run(
                ["git", "cat-file", "-p", f"{commit}:feeds/hn-small-sites-score-1.xml"],
                capture_output=True,
                text=True,
                cwd=hn_small_sites_feed_repo,
            )
            if res_git_show.returncode != 0:
                logger.error(f"Error in commit: {commit}")
                logger.error(res_git_show.stderr)
                continue
            generated_feed = re.sub(
                r"[\x00-\x08\x0b\x0c\x0e-\x1F\uD800-\uDFFF\uFFFE\uFFFF]",
                "",
                res_git_show.stdout,
            )
            try:
                feed = etree.fromstring(
                    generated_feed, parser=etree.XMLParser(huge_tree=True, recover=True)
                )
            except etree.XMLSyntaxError as e:
                logger.error(f"Error in commit: {commit}")
                logger.error(e)
                continue
            new_guids = set()
            for item in feed.iter("item"):
                try:
                    guid = item.find("guid").text
                    new_guids.add(guid)
                    if guid in prev_guids:
                        continue
                    title = item.find("title").text.strip()
                    link = item.find("link").text
                    pub_date = item.find("pubDate").text
                    description = item.find("description").text
                    yield FeedItem(
                        guid=guid,
                        title=title,
                        description=description,
                        link=link,
                        pub_date=pub_date,
                        last_source_commit=commit,
                    )
                except Exception as e:
                    logger.error(f"Error in an item in commit: {commit}, item: {item}")
                    logger.error(e)
                    continue
            prev_guids = new_guids
        except Exception as e:
            logger.error(f"Error in commit: {commit}")
            raise e


metadata_regex = re.compile('Score (\d+) \| Comments (\d+) \(<a href="(\S+?)"')


def process_feed_item(feed_item: FeedItem) -> HNEntry:
    metadata_match = metadata_regex.search(feed_item.description, endpos=1024)
    if not metadata_match:
        logger.error(
            f"Could not find metadata in {feed_item.guid}, skipping:\n{feed_item.description}"  # noqa: E501
        )
        return
    num_score = int(metadata_match.group(1))
    num_comments = int(metadata_match.group(2))
    thread_link = metadata_match.group(3)
    try:
        text = feed_item.description.split("<!-- hnss:readable-content --><hr/>")[1]
    except IndexError:
        text = feed_item.description.split("<!-- hnss:readable-content --><hr />")[1]
    return HNEntry(
        guid=feed_item.guid,
        pub_date=feed_item.pub_date,
        num_score=num_score,
        num_comments=num_comments,
        thread_link=thread_link,
        last_source_commit=feed_item.last_source_commit,
        title=feed_item.title,
        link=feed_item.link,
        text=text,
    )


def main():
    parser = argparse.ArgumentParser(
        description="CLI program for HN_SMALL_SITES_FEED_REPO"
    )
    parser.add_argument(
        "HN_SMALL_SITES_FEED_REPO", type=str, help="Path to HN_SMALL_SITES_FEED_REPO"
    )
    parser.add_argument("--until", type=str, help="Commit to scan up until (exclusive)")
    args = parser.parse_args()
    for feed_item in yield_feed_items(args.HN_SMALL_SITES_FEED_REPO, args.until):
        hne = process_feed_item(feed_item)
        print(json.dumps(asdict(hne)))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )
    main()
