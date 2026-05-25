from pathlib import Path
import sys


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.models.code_chunk import CodeChunk  # noqa: E402
from app.services.vector_store_service import VectorService  # noqa: E402


TEST_CHROMA_DIR = BACKEND_DIR / "chroma_db_test"
TEST_COLLECTION_NAME = "test_code_chunks"


def build_test_chunks() -> list[CodeChunk]:
    """Create small code chunks with clear topics for retrieval testing."""
    return [
        CodeChunk(
            content="\n".join(
                [
                    "// Parse HTTP request line and headers.",
                    "HttpRequest parseHttpRequest(const std::string& raw_request) {",
                    "    HttpRequest request;",
                    "    request.method = readMethod(raw_request);",
                    "    request.path = readPath(raw_request);",
                    "    return request;",
                    "}",
                ]
            ),
            file_path="src/http_request.cpp",
            start_line=10,
            end_line=16,
        ),
        CodeChunk(
            content="\n".join(
                [
                    "// Manage user sessions with a session id cookie.",
                    "Session createSession(const std::string& user_name) {",
                    "    Session session;",
                    "    session.user_name = user_name;",
                    "    return session;",
                    "}",
                ]
            ),
            file_path="src/session_manager.cpp",
            start_line=22,
            end_line=27,
        ),
        CodeChunk(
            content="\n".join(
                [
                    "// Check whether a Gomoku player has five stones in a row.",
                    "bool hasWinner(const Board& board, Stone stone) {",
                    "    return checkRows(board, stone) || checkColumns(board, stone);",
                    "}",
                ]
            ),
            file_path="src/gomoku.cpp",
            start_line=40,
            end_line=43,
        ),
    ]


def print_search_results(results) -> None:
    """Print returned chunks in a readable format for manual inspection."""
    for index, result in enumerate(results, start=1):
        metadata = result["metadata"]

        print(f"Result {index}")
        print(f"file_path: {metadata['file_path']}")
        print(f"start_line: {metadata['start_line']}")
        print(f"end_line: {metadata['end_line']}")
        print(f"distance: {result['distance']}")
        print("content preview:")
        print("\n".join(result["content"].splitlines()[:3]))
        print("-" * 40)


def test_add_chunks() -> None:
    """Check that chunks can be written into ChromaDB."""
    service = VectorService(
        persist_dir=TEST_CHROMA_DIR,
        collection_name=TEST_COLLECTION_NAME,
    )
    service.clear_collection()

    chunks = build_test_chunks()
    added_count = service.add_chunks(chunks)

    assert added_count == 3
    assert service.collection.count() == 3

    print("Test 1: add chunks")
    print(f"Added chunks: {added_count}")
    print(f"Collection count: {service.collection.count()}")
    print()


def test_query_chunks() -> None:
    """Check that a question can retrieve a related code chunk."""
    service = VectorService(
        persist_dir=TEST_CHROMA_DIR,
        collection_name=TEST_COLLECTION_NAME,
    )

    question = "Where is the HTTP request parsed?"
    results = service.query(question, top_k=2)

    print("Test 2: query chunks")
    print(f"Question: {question}")
    print_search_results(results)

    assert len(results) == 2
    assert results[0]["metadata"]["file_path"] == "src/http_request.cpp"


def main() -> None:
    test_add_chunks()
    test_query_chunks()

    print("All vector service checks passed.")


if __name__ == "__main__":
    main()
