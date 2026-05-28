from typing import Any, Dict, List

from app.services.llm_service import LLMService
from app.services.vector_store_service import VectorService


class RAGService:
    """Run the full retrieval-augmented question answering flow."""

    def __init__(
        self,
        vector_service: VectorService | None = None,
        llm_service: LLMService | None = None,
    ) -> None:
        self.vector_service = vector_service or VectorService()
        self.llm_service = llm_service or LLMService()

    def ask(self, question: str, top_k: int = 3) -> Dict[str, Any]:
        """
        Answer a user question by retrieving code chunks first, then asking DeepSeek.

        DeepSeek receives only the retrieved chunks as code context. If those
        chunks are not enough, the prompt tells DeepSeek to say so clearly.
        """
        matches = self.vector_service.query(question, top_k=top_k)

        if not matches:
            return {
                "question": question,
                "answer": "当前检索到的代码不足以判断",
                "references": [],
            }

        prompt = build_rag_prompt(question, matches)
        answer = self.llm_service.ask(prompt)

        return {
            "question": question,
            "answer": answer,
            "references": build_references(matches),
        }


def build_rag_prompt(question: str, matches: List[Dict[str, Any]]) -> str:
    """Build a simple prompt that keeps the answer grounded in retrieved code."""
    context_blocks = []

    for index, match in enumerate(matches, start=1):
        metadata = match["metadata"]
        file_path = metadata.get("file_path", "unknown")
        start_line = metadata.get("start_line", "?")
        end_line = metadata.get("end_line", "?")

        context_blocks.append(
            "\n".join(
                [
                    f"[{index}] 文件: {file_path}, 行号: {start_line}-{end_line}",
                    "```cpp",
                    match["content"],
                    "```",
                ]
            )
        )

    code_context = "\n\n".join(context_blocks)

    return f"""你是一个 C++ 项目代码问答助手。

请严格遵守以下要求：
1. 只能基于下面提供的代码片段回答问题。
2. 如果代码片段不足以回答问题，请明确说明“当前检索到的代码不足以判断”。
3. 回答中尽量包含参考的文件路径和行号。
4. 不要编造没有出现在代码片段中的信息。

用户问题：
{question}

检索到的代码片段：
{code_context}

请基于以上代码片段回答。"""


def build_references(matches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return file and line references for the chunks used in the answer."""
    references = []

    for match in matches:
        metadata = match["metadata"]
        references.append(
            {
                "file_path": metadata.get("file_path"),
                "start_line": metadata.get("start_line"),
                "end_line": metadata.get("end_line"),
                "distance": match.get("distance"),
            }
        )

    return references
