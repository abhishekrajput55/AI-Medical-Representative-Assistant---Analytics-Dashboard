"""
NOTE: This file is no longer used.

We originally planned to compute embeddings ourselves using
sentence-transformers (which depends on PyTorch, a ~370MB download).
To keep the install lightweight and reliable on slower connections,
we switched to ChromaDB's own built-in embedding function instead —
see vectorstore.py. It uses a small ONNX model internally and needs
no PyTorch at all. Kept here only as a reference/comment.
"""
