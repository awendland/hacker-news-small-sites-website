import argparse
import json

import chromadb
from langchain_community.embeddings import HuggingFaceBgeEmbeddings

_embedder = None


def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = HuggingFaceBgeEmbeddings(
            model_name="BAAI/bge-small-en", encode_kwargs={"normalize_embeddings": True}
        )
    return _embedder, "BAAI/bge-small-en"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("data_file_path", help="Path to the JSONL data file")
    parser.add_argument("query", help="Query to embed and search for in the DB")
    args = parser.parse_args()

    client = chromadb.PersistentClient(path="./chroma")
    collection = client.get_collection(name="hn_small_sites_feed_repo")
    embedder, _ = get_embedder()
    query_embeddings = embedder.embed_query(args.query)
    results = collection.query(query_embeddings)
    print(results)
    remaining_ids = set([id.split(":")[0] for id in results["ids"][0]])
    with open(args.data_file_path, "r") as file:
        for line in file:
            for r in remaining_ids:
                if r in line:
                    data = json.loads(line)
                    data.pop("text")
                    print(json.dumps(data, indent=2))
                    remaining_ids.remove(r)
                    break
            if not remaining_ids:
                break
