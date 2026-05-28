import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.services.chunk_service import chunk_code_file  # noqa: E402
from app.services.vector_store_service import (  # noqa: E402
    DEFAULT_CHROMA_DIR,
    DEFAULT_COLLECTION_NAME,
    VectorService,
)


CPP_FILE_EXTENSIONS = {".cpp", ".cc", ".cxx", ".h", ".hpp"}
IGNORED_DIRS = {".git", "build", "cmake-build", "cmake-build-debug", "cmake-build-release"}


def should_ignore(path: Path) -> bool:
    return any(part.lower() in IGNORED_DIRS for part in path.parts)


def find_cpp_files(project_dir: Path) -> list[Path]:
    cpp_files: list[Path] = []

    for path in project_dir.rglob("*"):
        relative_path = path.relative_to(project_dir)

        if should_ignore(relative_path):
            continue

        if path.is_file() and path.suffix.lower() in CPP_FILE_EXTENSIONS:
            cpp_files.append(path)

    return sorted(cpp_files)


def index_project(project_dir: Path) -> None:
    if not project_dir.exists():
        raise FileNotFoundError(f"Project directory does not exist: {project_dir}")

    if not project_dir.is_dir():
        raise NotADirectoryError(f"Project path is not a directory: {project_dir}")

    source_files = find_cpp_files(project_dir)
    chunks = []

    for source_file in source_files:
        relative_path = source_file.relative_to(project_dir).as_posix()
        content = source_file.read_text(encoding="utf-8", errors="ignore")
        chunks.extend(chunk_code_file(relative_path, content))

    vector_service = VectorService(
        persist_dir=DEFAULT_CHROMA_DIR,
        collection_name=DEFAULT_COLLECTION_NAME,
    )
    vector_service.add_chunks(chunks)

    print(f"Scanned source files: {len(source_files)}")
    print(f"Generated chunks: {len(chunks)}")
    print(f"ChromaDB path: {vector_service.persist_dir}")
    print(f"Collection name: {vector_service.collection_name}")
    print(f"Collection count: {vector_service.collection.count()}")


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/index_project.py <cpp_project_dir>")
        raise SystemExit(1)

    project_dir = Path(sys.argv[1]).expanduser().resolve()
    index_project(project_dir)


if __name__ == "__main__":
    main()
