import argparse
import json
import sqlite3

import chromadb

parser = argparse.ArgumentParser()
parser.add_argument("data_path", help="Path to the JSONL data file")
parser.add_argument(
    "embeddings_path",
    help="Path to an embeddings file generated with entries-to-embeddings.py, corresponding to the data file",  # noqa: E501
)
args = parser.parse_args()

vector_client = chromadb.PersistentClient(path="./chroma")
vector_collection = vector_client.get_or_create_collection(name="hn_small_sites")
db_client = sqlite3.connect("./data.db")

db_client.execute(
    """
    CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        content TEXT
    )
"""
)


def count_lines_in_file(file_path: str) -> int:
    with open(file_path, "r") as file:
        return sum(1 for _ in file)


count_data = count_lines_in_file(args.data_path)
count_embeddings = count_lines_in_file(args.embeddings_path)

if count_data != count_embeddings:
    raise ValueError(
        f"Data file has {count_data} lines, while embeddings file has {count_embeddings} lines. They should have the same number of lines."  # noqa: E501
    )


with open(args.data_path, "r") as file_data:
    with open(args.embeddings_path, "r") as file_embeddings:
        for i_l, (line_data, line_embeddings) in enumerate(
            zip(file_data, file_embeddings)
        ):
            data = json.loads(line_embeddings)
            id = data["id"]
            embeddings = next(iter(data["embeddings"].values()))
            for i_e, embedding in enumerate(embeddings):
                vector_collection.add(
                    ids=f"{id}:{i_e}",
                    embeddings=embedding,
                    metadatas={"id": id, "index": i_e},
                )
            db_client.execute(
                """
                INSERT OR IGNORE INTO documents (id, content) VALUES (?, ?)
            """,
                (id, line_data),
            )
            db_client.commit()
            print(
                f"Processing {i_l+1} out of {count_data}", end="\r"
            )  # Print i out of count on the same line
