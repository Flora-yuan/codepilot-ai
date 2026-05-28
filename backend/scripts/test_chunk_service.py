# Path:
# 用于处理文件路径
from pathlib import Path

# sys:
# 用于修改 Python 模块搜索路径
import sys


# 获取 backend 根目录
# __file__ 表示当前文件
# resolve() 获取绝对路径
# parents[1] 表示上两级目录
BACKEND_DIR = Path(__file__).resolve().parents[1]

# 将 backend 目录加入 Python 导入路径
# 否则无法导入 app.services 下的模块
sys.path.insert(0, str(BACKEND_DIR))


# 导入真正要测试的代码切分函数
from app.services.chunk_service import chunk_code_file  # noqa: E402


def build_fake_cpp_code(line_count: int) -> str:
    """
    构造假的 C++ 代码文件。

    参数:
        line_count:
            要生成多少行代码

    返回:
        一个字符串，每行都是简单的 C++ 变量定义

    示例:
        int value_1 = 1;
        int value_2 = 2;
        ...
    """

    return "\n".join(
        f"int value_{line_number} = {line_number};"
        for line_number in range(1, line_count + 1)
    )


def preview_chunk_content(content: str, line_count: int = 3) -> str:
    """
    获取 chunk 前几行内容用于预览。

    为什么这样做:
        chunk 可能很长，
        打印全部内容会影响测试输出可读性。

    参数:
        content:
            chunk 的完整文本

        line_count:
            预览多少行（默认 3 行）

    返回:
        前 line_count 行组成的字符串
    """

    return "\n".join(content.splitlines()[:line_count])


def print_chunk_summary(chunks) -> None:
    """
    打印 chunk 的概要信息。

    输出内容:
        - chunk 数量
        - 文件路径
        - 起始行号
        - 结束行号
        - 内容预览
    """

    print(f"Total chunks: {len(chunks)}")
    print()

    # enumerate(..., start=1)
    # 让 chunk 编号从 1 开始
    for index, chunk in enumerate(chunks, start=1):

        print(f"Chunk {index}")

        # chunk 来自哪个文件
        print(f"file_path: {chunk.file_path}")

        # chunk 起始行
        print(f"start_line: {chunk.start_line}")

        # chunk 结束行
        print(f"end_line: {chunk.end_line}")

        # chunk 内容预览
        print("content preview:")
        print(preview_chunk_content(chunk.content))

        print("-" * 40)


def test_large_cpp_file() -> None:
    """
    测试:
        大型 C++ 文件能否正确切分。

    测试重点:
        1. 是否正确生成多个 chunk
        2. chunk 的行号是否正确
        3. overlap 是否正确生效
    """

    # 构造 200 行假的 C++ 代码
    fake_cpp = build_fake_cpp_code(200)

    # 调用 chunk 切分函数
    chunks = chunk_code_file(
        file_path="example.cpp",
        content=fake_cpp,

        # 每个 chunk 最大 80 行
        chunk_size=80,

        # chunk 之间重叠 10 行
        overlap=10,
    )

    print("Test 1: large C++ file")
    print_chunk_summary(chunks)

    # =========================
    # 检查 chunk 数量是否正确
    # =========================

    # 200 行应该被切成:
    #
    # chunk1: 1   - 80
    # chunk2: 71  - 150
    # chunk3: 141 - 200
    #
    assert len(chunks) == 3

    # =========================
    # 检查 chunk1 行号
    # =========================
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == 80

    # =========================
    # 检查 chunk2 行号
    # =========================
    assert chunks[1].start_line == 71
    assert chunks[1].end_line == 150

    # =========================
    # 检查 chunk3 行号
    # =========================
    assert chunks[2].start_line == 141
    assert chunks[2].end_line == 200

    # 将 chunk 内容按行拆开
    first_chunk_lines = chunks[0].content.splitlines()
    second_chunk_lines = chunks[1].content.splitlines()
    third_chunk_lines = chunks[2].content.splitlines()

    # =========================
    # 检查 overlap 是否正确
    # =========================

    # chunk1 最后 10 行
    # 应该等于
    # chunk2 前 10 行
    assert first_chunk_lines[-10:] == second_chunk_lines[:10]

    # chunk2 最后 10 行
    # 应该等于
    # chunk3 前 10 行
    assert second_chunk_lines[-10:] == third_chunk_lines[:10]

    # 打印 overlap 结果
    print("Overlap between chunk 1 and chunk 2:")

    print(
        f"chunk 1 overlap range: "
        f"{first_chunk_lines[-10]} ... {first_chunk_lines[-1]}"
    )

    print(
        f"chunk 2 overlap range: "
        f"{second_chunk_lines[0]} ... {second_chunk_lines[9]}"
    )

    print()

    print("Overlap between chunk 2 and chunk 3:")

    print(
        f"chunk 2 overlap range: "
        f"{second_chunk_lines[-10]} ... {second_chunk_lines[-1]}"
    )

    print(
        f"chunk 3 overlap range: "
        f"{third_chunk_lines[0]} ... {third_chunk_lines[9]}"
    )

    print()


def test_short_cpp_file() -> None:
    """
    测试:
        短文件是否只生成一个 chunk。
    """

    print("Test 2: short C++ header file")

    # 只有 5 行代码
    short_file_chunks = chunk_code_file(
        "short.hpp",
        build_fake_cpp_code(5),
    )

    # 应该只生成一个 chunk
    assert len(short_file_chunks) == 1

    # 行号应该正确
    assert short_file_chunks[0].start_line == 1
    assert short_file_chunks[0].end_line == 5

    print_chunk_summary(short_file_chunks)


def test_empty_cpp_file() -> None:
    """
    测试:
        空文件是否返回空列表。
    """

    print("Test 3: empty C++ file")

    # 空内容
    empty_file_chunks = chunk_code_file("empty.cpp", "")

    # 应该返回空列表
    assert empty_file_chunks == []

    print("Empty file chunks: []")
    print()


def test_non_cpp_file() -> None:
    """
    测试:
        非 C/C++ 文件是否会被忽略。
    """

    print("Test 4: non-C++ file")

    fake_cpp = build_fake_cpp_code(20)

    # 虽然内容像 C++，
    # 但文件名是 txt
    non_cpp_chunks = chunk_code_file("notes.txt", fake_cpp)

    # 应该被忽略
    assert non_cpp_chunks == []

    print("Non-C++ file chunks: []")
    print()


def test_invalid_settings() -> None:
    """
    测试:
        非法 chunk 参数是否会抛出异常。
    """

    print("Test 5: invalid chunk settings")

    fake_cpp = build_fake_cpp_code(20)

    # =========================
    # 测试 chunk_size = 0
    # =========================

    try:
        chunk_code_file(
            "bad.cpp",
            fake_cpp,
            chunk_size=0,
        )

    except ValueError as error:

        # 检查错误信息
        assert str(error) == "chunk_size must be greater than 0"

        print(f"chunk_size=0 error: {error}")

    else:
        # 如果没报错，测试失败
        raise AssertionError(
            "chunk_size=0 should raise ValueError"
        )

    # =========================
    # 测试 overlap >= chunk_size
    # =========================

    try:
        chunk_code_file(
            "bad.cpp",
            fake_cpp,
            chunk_size=10,
            overlap=10,
        )

    except ValueError as error:

        # overlap 必须小于 chunk_size
        assert str(error) == "overlap must be smaller than chunk_size"

        print(f"overlap=chunk_size error: {error}")

    else:
        raise AssertionError(
            "overlap >= chunk_size should raise ValueError"
        )

    print()


def main() -> None:
    """
    运行所有测试。
    """

    # 测试大型文件切分
    test_large_cpp_file()

    # 测试短文件
    test_short_cpp_file()

    # 测试空文件
    test_empty_cpp_file()

    # 测试非 C++ 文件
    test_non_cpp_file()

    # 测试非法参数
    test_invalid_settings()

    print("All chunk service checks passed.")


# Python 程序入口
# 只有直接运行当前文件时才执行 main()
if __name__ == "__main__":
    main()