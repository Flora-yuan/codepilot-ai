import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from backend.app.services.agent_workflow import LangGraphRAGService


router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    question: str


class CodeReference(BaseModel):
    file_path: str | None = None
    start_line: int | None = None
    end_line: int | None = None


class ChatResponse(BaseModel):
    question: str
    answer: str
    references: list[CodeReference]


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        result = get_agent_service().graph.invoke(
            {
                "question": question,
                "contexts": [],
                "prompt": "",
                "answer": "",
            }
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ChatResponse(
        question=question,
        answer=result.get("answer", ""),
        references=_build_references(result.get("contexts", [])),
    )


@lru_cache(maxsize=1)
def get_agent_service() -> LangGraphRAGService:
    return LangGraphRAGService()


def _build_references(contexts: list[Any]) -> list[CodeReference]:
    references: list[CodeReference] = []

    for context in contexts:
        if not isinstance(context, dict):
            continue

        metadata = context.get("metadata")
        if not isinstance(metadata, dict):
            continue

        references.append(
            CodeReference(
                file_path=metadata.get("file_path"),
                start_line=_to_int(metadata.get("start_line")),
                end_line=_to_int(metadata.get("end_line")),
            )
        )

    return references


def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
