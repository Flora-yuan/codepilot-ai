from dataclasses import dataclass
from pathlib import Path


CPP_EXTENSIONS = {".cpp", ".cc", ".h", ".hpp"}
IGNORED_DIRS = {".git", "build", "cmake-build", "cmake-build-debug", "cmake-build-release"}


@dataclass
class SourceFile:
    relative_path: str
    content: str
    line_count: int
    size: int


def should_ignore_path(path: Path) -> bool:
    return any(part.lower() in IGNORED_DIRS for part in path.parts)


def is_cpp_source_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in CPP_EXTENSIONS


def load_cpp_source_files(project_dir: Path) -> list[SourceFile]:
    source_files: list[SourceFile] = []

    for path in project_dir.rglob("*"):
        relative_path = path.relative_to(project_dir)

        if should_ignore_path(relative_path):
            continue

        if not is_cpp_source_file(path):
            continue

        content = path.read_text(encoding="utf-8", errors="ignore")
        source_files.append(
            SourceFile(
                relative_path=relative_path.as_posix(),
                content=content,
                line_count=len(content.splitlines()),
                size=path.stat().st_size,
            )
        )

    return sorted(source_files, key=lambda source_file: source_file.relative_path)
