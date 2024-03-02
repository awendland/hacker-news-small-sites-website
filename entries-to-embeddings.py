import argparse
import json
from typing import List

import html2text
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from llama_index.core.node_parser import SentenceSplitter

_embedder = None


def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = HuggingFaceBgeEmbeddings(
            model_name="BAAI/bge-small-en", encode_kwargs={"normalize_embeddings": True}
        )
    return _embedder, "BAAI/bge-small-en"


ss = SentenceSplitter(chunk_size=256, chunk_overlap=64)


def create_embedding(text: str) -> List[List[float]]:
    embedder, name = get_embedder()
    embeddings = {}
    embeddings[name] = []
    for s in ss.split_text(text):
        embeddings[name].extend(embedder.embed_documents([s]))
    return embeddings


def process_hn_entries(file_path):
    with open(file_path, "r") as file:
        for line in file:
            entry = json.loads(line)
            text = html2text.html2text(entry.get("text", ""))
            print(
                json.dumps({"id": entry["guid"], "embeddings": create_embedding(text)})
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl_file_path", help="Path to the JSONL file")
    args = parser.parse_args()

    process_hn_entries(args.jsonl_file_path)
