from langchain_community.embeddings import HuggingFaceBgeEmbeddings

_embedder = None


def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = HuggingFaceBgeEmbeddings(
            model_name="BAAI/bge-small-en", encode_kwargs={"normalize_embeddings": True}
        )
    return _embedder, "BAAI/bge-small-en"
