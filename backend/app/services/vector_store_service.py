from pathlib import Path
from typing import Any, Dict, List

import chromadb

from app.models.code_chunk import CodeChunk


DEFAULT_COLLECTION_NAME = "code_chunks"
DEFAULT_CHROMA_DIR = Path(__file__).resolve().parents[2] / "chroma_db"


class VectorService:
    """Store and search code chunks in a local ChromaDB database."""

    def __init__(
        self,
        persist_dir: str | Path = DEFAULT_CHROMA_DIR,
        collection_name: str = DEFAULT_COLLECTION_NAME,
    ) -> None:
        self.persist_dir = Path(persist_dir)
        self.collection_name = collection_name
        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add_chunks(self, chunks: List[CodeChunk]) -> int:
        """
        Save code chunks into ChromaDB.

        ChromaDB stores the chunk text as the searchable document, and stores
        file location information in metadata so search results can point back
        to the original source file.
        """
        if not chunks:
            return 0

        ids = [self._build_chunk_id(chunk) for chunk in chunks]
        documents = [chunk.content for chunk in chunks]
        metadatas = [
            {
                "file_path": chunk.file_path,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
            }
            for chunk in chunks
        ]

        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )

        return len(chunks)

    def query(self, question: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Search for the most relevant code chunks for a user question.

        `top_k` controls how many matching chunks are returned.
        """
        if top_k <= 0:
            raise ValueError("top_k must be greater than 0")

        results = self.collection.query(
            query_texts=[question],
            n_results=top_k,
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        matches: List[Dict[str, Any]] = []
        for document, metadata, distance in zip(documents, metadatas, distances):
            matches.append(
                {
                    "content": document,
                    "metadata": metadata,
                    "distance": distance,
                }
            )

        return matches

    def clear_collection(self) -> None:
        """Delete and recreate the collection. Useful for simple test scripts."""
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.get_or_create_collection(name=self.collection_name)

    def _build_chunk_id(self, chunk: CodeChunk) -> str:
        """Build a stable id so the same chunk can be updated safely."""
        return f"{chunk.file_path}:{chunk.start_line}:{chunk.end_line}"
