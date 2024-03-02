import argparse
import json

import chromadb

parser = argparse.ArgumentParser()
parser.add_argument(
    "embeddings_path",
    help="Path to an embeddings file generated with entries-to-embeddings.py",
)
args = parser.parse_args()

# Rest of the code

client = chromadb.PersistentClient(path="./chroma")
collection = client.get_or_create_collection(name="hn_small_sites_feed_repo")

count = 0
with open(args.embeddings_path, "r") as file:
    for line in file:
        count += 1

with open(args.embeddings_path, "r") as file:
    for i_l, line in enumerate(file):
        data = json.loads(line)
        id = data["id"]

        embeddings = next(iter(data["embeddings"].values()))
        for i_e, embedding in enumerate(embeddings):
            collection.add(
                ids=f"{id}:{i_e}",
                embeddings=embedding,
                metadatas={"id": id, "index": i_e},
            )

        print(
            f"Processing {i_l+1} out of {count}", end="\r"
        )  # Print i out of count on the same line
