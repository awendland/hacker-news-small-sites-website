import argparse
import logging
import os.path
import sys
from itertools import islice

from ingest import HNSmallSiteFeedRepo
from llama_index.core import (
    Settings,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
from llama_index.embeddings.openai import OpenAIEmbedding

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

parser = argparse.ArgumentParser(description="CLI program for HN_SMALL_SITES_FEED_REPO")
parser.add_argument(
    "HN_SMALL_SITES_FEED_REPO", type=str, help="Path to HN_SMALL_SITES_FEED_REPO"
)
args = parser.parse_args()
hn_small_sites_feed_repo = args.HN_SMALL_SITES_FEED_REPO

Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")

PERSIST_DIR = "./storage"
if not os.path.exists(PERSIST_DIR):
    documents = HNSmallSiteFeedRepo(hn_small_sites_feed_repo).lazy_load_data()
    index = VectorStoreIndex.from_documents([next(documents)])
    for d in islice(documents, 100):
        index.insert(d)
    index.storage_context.persist(persist_dir=PERSIST_DIR)
else:
    storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
    index = load_index_from_storage(storage_context)

retriever = index.as_retriever()
while True:
    response = retriever.retrieve(input("Enter a query: "))
    print(response)
