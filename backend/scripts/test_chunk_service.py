from pathlib import Path
import sys


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.services.chunk_service import chunk_code_file  # noqa: E402


def build_fake_cpp_code(line_count: int) -> str:
    """Create simple fake C++ code with predictable line numbers."""
    return "\n".join(f"int value_{line_number} = {line_number};" for line_number in range(1, line_count + 1))


def preview_chunk_content(content: str, line_count: int = 3) -> str:
    """Return the first few lines of a chunk for readable test output."""
    return "\n".join(content.splitlines()[:line_count])


def print_chunk_summary(chunks) -> None:
    """Print each chunk's source location and a small content preview."""
    print(f"Total chunks: {len(chunks)}")
    print()

    for index, chunk in enumerate(chunks, start=1):
        print(f"Chunk {index}")
        print(f"file_path: {chunk.file_path}")
        print(f"start_line: {chunk.start_line}")
        print(f"end_line: {chunk.end_line}")
        print("content preview:")
        print(preview_chunk_content(chunk.content))
        print("-" * 40)


def test_large_cpp_file() -> None:
    """Check that a 200-line file is split into overlapping chunks."""
    fake_cpp = build_fake_cpp_code(200)
    chunks = chunk_code_file(
        file_path="example.cpp",
        content=fake_cpp,
        chunk_size=80,
        overlap=10,
    )

    print("Test 1: large C++ file")
    print_chunk_summary(chunks)

    assert len(chunks) == 3
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == 80
    assert chunks[1].start_line == 71
    assert chunks[1].end_line == 150
    assert chunks[2].start_line == 141
    assert chunks[2].end_line == 200

    first_chunk_lines = chunks[0].content.splitlines()
    second_chunk_lines = chunks[1].content.splitlines()
    third_chunk_lines = chunks[2].content.splitlines()

    assert first_chunk_lines[-10:] == second_chunk_lines[:10]
    assert second_chunk_lines[-10:] == third_chunk_lines[:10]

    print("Overlap between chunk 1 and chunk 2:")
    print(f"chunk 1 overlap range: {first_chunk_lines[-10]} ... {first_chunk_lines[-1]}")
    print(f"chunk 2 overlap range: {second_chunk_lines[0]} ... {second_chunk_lines[9]}")
    print()

    print("Overlap between chunk 2 and chunk 3:")
    print(f"chunk 2 overlap range: {second_chunk_lines[-10]} ... {second_chunk_lines[-1]}")
    print(f"chunk 3 overlap range: {third_chunk_lines[0]} ... {third_chunk_lines[9]}")
    print()


def test_short_cpp_file() -> None:
    """Check that a short file produces exactly one chunk."""
    print("Test 2: short C++ header file")

    short_file_chunks = chunk_code_file("short.hpp", build_fake_cpp_code(5))
    assert len(short_file_chunks) == 1
    assert short_file_chunks[0].start_line == 1
    assert short_file_chunks[0].end_line == 5

    print_chunk_summary(short_file_chunks)


def test_empty_cpp_file() -> None:
    """Check that an empty C++ file produces no chunks."""
    print("Test 3: empty C++ file")

    empty_file_chunks = chunk_code_file("empty.cpp", "")
    assert empty_file_chunks == []

    print("Empty file chunks: []")
    print()


def test_non_cpp_file() -> None:
    """Check that non-C/C++ files are ignored."""
    print("Test 4: non-C++ file")

    fake_cpp = build_fake_cpp_code(20)
    non_cpp_chunks = chunk_code_file("notes.txt", fake_cpp)
    assert non_cpp_chunks == []

    print("Non-C++ file chunks: []")
    print()


def test_invalid_settings() -> None:
    """Check that invalid chunk settings raise clear errors."""
    print("Test 5: invalid chunk settings")

    fake_cpp = build_fake_cpp_code(20)

    try:
        chunk_code_file("bad.cpp", fake_cpp, chunk_size=0)
    except ValueError as error:
        assert str(error) == "chunk_size must be greater than 0"
        print(f"chunk_size=0 error: {error}")
    else:
        raise AssertionError("chunk_size=0 should raise ValueError")

    try:
        chunk_code_file("bad.cpp", fake_cpp, chunk_size=10, overlap=10)
    except ValueError as error:
        assert str(error) == "overlap must be smaller than chunk_size"
        print(f"overlap=chunk_size error: {error}")
    else:
        raise AssertionError("overlap >= chunk_size should raise ValueError")

    print()


def main() -> None:
    test_large_cpp_file()
    test_short_cpp_file()
    test_empty_cpp_file()
    test_non_cpp_file()
    test_invalid_settings()

    print("All chunk service checks passed.")


if __name__ == "__main__":
    main()
