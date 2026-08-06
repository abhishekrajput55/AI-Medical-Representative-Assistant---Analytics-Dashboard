"""
Vector store: the 'smart filing cabinet' that stores product text
and finds the most relevant entries for a given question.

We let ChromaDB handle embeddings itself using its built-in default
embedding function (a small ONNX-based MiniLM model). This avoids
needing PyTorch/sentence-transformers as a dependency — same
underlying idea (MiniLM), just a lighter-weight version that
downloads in seconds instead of many minutes.
"""

import chromadb

_CHROMA_PATH = "/app/chroma_data"
_COLLECTION_NAME = "products"

_client = chromadb.PersistentClient(path=_CHROMA_PATH)
# No embedding_function specified = Chroma uses its built-in default
# (all-MiniLM-L6-v2, ONNX version) automatically, computed lazily
# the first time it's actually needed.
_collection = _client.get_or_create_collection(name=_COLLECTION_NAME)


def product_to_document(product) -> str:
    """
    Flattens a Product database row into one block of plain text.
    This is what actually gets embedded and searched — so it needs
    to contain every fact we want the chatbot to be able to answer
    questions about.
    """
    parts = [
        f"Product: {product.brand_name}",
        f"Generic name: {product.generic_name}" if product.generic_name else "",
        f"Composition: {product.composition}" if product.composition else "",
        f"Indications (what it treats): {product.indications}" if product.indications else "",
        f"Contraindications (when NOT to use it): {product.contraindications}" if product.contraindications else "",
        f"Side effects: {product.side_effects}" if product.side_effects else "",
        f"Competitors: {product.competitors}" if product.competitors else "",
        f"Pack size: {product.pack_size}" if product.pack_size else "",
    ]
    return "\n".join([part for part in parts if part])


def upsert_product(product) -> None:
    """
    Adds or updates one product in the vector store. 'Upsert' =
    update if it exists, insert if it doesn't — avoids duplicates
    when a product is edited. We pass plain text via `documents`;
    Chroma computes the embedding internally.
    """
    document_text = product_to_document(product)
    _collection.upsert(
        ids=[str(product.id)],
        documents=[document_text],
        metadatas=[{"brand_name": product.brand_name}],
    )


def delete_product(product_id) -> None:
    _collection.delete(ids=[str(product_id)])


def reindex_all_products(products: list) -> int:
    """Rebuilds the entire vector store from scratch. Used after bulk changes."""
    if not products:
        return 0
    ids = [str(p.id) for p in products]
    documents = [product_to_document(p) for p in products]
    metadatas = [{"brand_name": p.brand_name} for p in products]
    _collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    return len(products)


def search_relevant_products(query: str, top_k: int = 3) -> list[dict]:
    """
    The core retrieval step: given a question, finds the top_k most
    semantically similar products. Returns their text + how similar
    they were (distance — lower means more similar).
    """
    if _collection.count() == 0:
        return []

    results = _collection.query(
        query_texts=[query],
        n_results=min(top_k, _collection.count()),
    )

    matches = []
    for i in range(len(results["ids"][0])):
        matches.append({
            "brand_name": results["metadatas"][0][i]["brand_name"],
            "document": results["documents"][0][i],
            "distance": results["distances"][0][i],
        })
    return matches
