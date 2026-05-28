from pathlib import Path
import sys

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
load_dotenv(BACKEND_DIR / ".env")

from app.models.code_chunk import CodeChunk  # noqa: E402
from app.services.rag_service import RAGService  # noqa: E402
from app.services.vector_store_service import VectorService  # noqa: E402


TEST_CHROMA_DIR = BACKEND_DIR / "chroma_db_rag_test"
TEST_COLLECTION_NAME = "test_rag_code_chunks"


def build_test_chunks() -> list[CodeChunk]:
    """Create test chunks that simulate code retrieved from a C++ project."""
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
    ]


def main() -> None:
    """
    Verify the complete RAG flow:
    question -> ChromaDB retrieval -> DeepSeek answer.
    """
    vector_service = VectorService(
        persist_dir=TEST_CHROMA_DIR,
        collection_name=TEST_COLLECTION_NAME,
    )
    vector_service.clear_collection()
    vector_service.add_chunks(build_test_chunks())

    rag_service = RAGService(vector_service=vector_service)

    question = "Where is the HTTP request parsed?"
    result = rag_service.ask(question, top_k=2)

    print("Question:")
    print(result["question"])
    print()

    print("Answer:")
    print(result["answer"])
    print()

    print("References:")
    for reference in result["references"]:
        print(
            f"- {reference['file_path']}:"
            f"{reference['start_line']}-{reference['end_line']}"
        )


if __name__ == "__main__":
    main()
