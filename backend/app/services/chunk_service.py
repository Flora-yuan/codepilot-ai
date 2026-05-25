from pathlib import Path
from typing import List

from app.models.code_chunk import CodeChunk


CPP_FILE_EXTENSIONS = {".cpp", ".cc", ".cxx", ".h", ".hpp"}


def chunk_code_file(
    file_path: str,
    content: str,
    chunk_size: int = 80,
    overlap: int = 10,
) -> List[CodeChunk]:
    """
    Split one C/C++ source file into smaller chunks by line count.

    Adjacent chunks share `overlap` lines so later retrieval can keep a little
    context when a function or class is split across chunk boundaries.
    """
    if not _is_cpp_file(file_path):
        return []

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")

    if overlap < 0:
        raise ValueError("overlap must be greater than or equal to 0")

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    lines = content.splitlines()
    if not lines:
        return []

    chunks: List[CodeChunk] = []
    step = chunk_size - overlap
    start_index = 0

    while start_index < len(lines):
        end_index = min(start_index + chunk_size, len(lines))
        chunk_lines = lines[start_index:end_index]

        chunks.append(
            CodeChunk(
                content="\n".join(chunk_lines),
                file_path=file_path,
                start_line=start_index + 1,
                end_line=end_index,
            )
        )

        if end_index == len(lines):
            break

        start_index += step

    return chunks


def _is_cpp_file(file_path: str) -> bool:
    """Return True only for C/C++ source and header file extensions."""
    return Path(file_path).suffix.lower() in CPP_FILE_EXTENSIONS
