import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.services.agent_workflow import LangGraphRAGService


def main() -> None:
    """Run a minimal manual check for the LangGraph RAG workflow."""
    question = "这个项目的 HTTP 请求是如何被处理的？"
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])

    service = LangGraphRAGService()
    answer = service.ask(question)

    print("Question:")
    print(question)
    print()
    print("LangGraph RAG answer:")
    print(answer)


if __name__ == "__main__":
    main()
