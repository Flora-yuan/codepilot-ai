from dataclasses import dataclass


@dataclass
class CodeChunk:
    """A small piece of source code with its original file location."""

    content: str
    file_path: str
    start_line: int
    end_line: int
