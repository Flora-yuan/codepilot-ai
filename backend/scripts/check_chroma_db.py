import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.services.vector_store_service import (  # noqa: E402
    DEFAULT_CHROMA_DIR,
    DEFAULT_COLLECTION_NAME,
    VectorService,
)


def main() -> None:
    service = VectorService(
        persist_dir=DEFAULT_CHROMA_DIR,
        collection_name=DEFAULT_COLLECTION_NAME,
    )

    print(f"ChromaDB path: {service.persist_dir}")
    print(f"Collection name: {service.collection_name}")
    print(f"Collection count: {service.collection.count()}")
    print()

    results = service.collection.get(
        limit=3,
        include=["documents", "metadatas"],
    )

    documents = results.get("documents", [])
    metadatas = results.get("metadatas", [])

    if not documents:
        print("No documents found in this collection.")
        return

    for index, (document, metadata) in enumerate(zip(documents, metadatas), start=1):
        print(f"Document {index}")
        print(f"file_path: {metadata.get('file_path')}")
        print(f"start_line: {metadata.get('start_line')}")
        print(f"end_line: {metadata.get('end_line')}")
        print("content preview:")
        print(document[:200])
        print("-" * 40)


if __name__ == "__main__":
    main()
