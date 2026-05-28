from importlib import import_module
from typing import Any, Dict, List, TypedDict

from langgraph.graph import END, START, StateGraph


class AgentState(TypedDict):
    """LangGraph workflow state shared by all RAG agent nodes."""

    question: str
    contexts: List[Any]
    prompt: str
    answer: str


class LangGraphRAGService:
    """A minimal LangGraph wrapper around the existing RAG question-answer flow."""

    def __init__(self) -> None:
        self.vector_service = self._create_vector_service()
        self.deepseek_service = self._create_deepseek_service()
        self.graph = self._build_graph()

    def _build_graph(self):
        """Create the simple retrieve -> build_prompt -> generate_answer workflow."""
        workflow = StateGraph(AgentState)

        workflow.add_node("retrieve", self.retrieve)
        workflow.add_node("build_prompt", self.build_prompt)
        workflow.add_node("generate_answer", self.generate_answer)

        workflow.add_edge(START, "retrieve")
        workflow.add_edge("retrieve", "build_prompt")
        workflow.add_edge("build_prompt", "generate_answer")
        workflow.add_edge("generate_answer", END)

        return workflow.compile()

    def retrieve(self, state: AgentState) -> Dict[str, Any]:
        """Retrieve code chunks related to the user's question from VectorService."""
        # This node keeps retrieval focused on the existing ChromaDB wrapper.
        question = state["question"]
        contexts = self.vector_service.query(question)
        return {"contexts": self._normalize_contexts(contexts)}

    def build_prompt(self, state: AgentState) -> Dict[str, str]:
        """Build the final DeepSeek prompt from the question and retrieved code chunks."""
        # This node only prepares text; it does not call the model.
        question = state["question"]
        contexts = state.get("contexts", [])
        context_text = self._format_contexts(contexts)

        prompt = f"""你是一个帮助初学者理解 C++ 项目的代码问答助手。

请只根据下面提供的代码片段回答问题。
如果代码片段中没有足够信息，请直接说明目前无法从已检索代码中确定。

【用户问题】
{question}

【相关代码片段】
{context_text}

请用清晰、适合初学者理解的中文回答。
"""
        return {"prompt": prompt}

    def generate_answer(self, state: AgentState) -> Dict[str, str]:
        """Call DeepSeekService with the prompt and store the generated answer."""
        # This node is the only place that talks to DeepSeek.
        prompt = state["prompt"]
        answer = self._call_deepseek(prompt)
        return {"answer": answer}

    def ask(self, question: str) -> str:
        """Run the LangGraph RAG workflow and return the final answer."""
        result = self.graph.invoke(
            {
                "question": question,
                "contexts": [],
                "prompt": "",
                "answer": "",
            }
        )
        return result["answer"]

    def _format_contexts(self, contexts: List[Any]) -> str:
        """Convert VectorService results into readable text for the LLM prompt."""
        if not contexts:
            return "未检索到相关代码片段。"

        formatted_chunks = []
        for index, context in enumerate(contexts, start=1):
            formatted_chunks.append(f"片段 {index}:\n{self._context_to_text(context)}")

        return "\n\n".join(formatted_chunks)

    def _context_to_text(self, context: Any) -> str:
        """Extract useful text from common VectorService result shapes."""
        if isinstance(context, str):
            return context

        if isinstance(context, dict):
            for key in ("content", "code", "text", "document", "chunk"):
                value = context.get(key)
                if value:
                    return str(value)
            return str(context)

        return str(context)

    def _normalize_contexts(self, contexts: Any) -> List[Any]:
        """Keep ChromaDB-style and list-style retrieval results easy to format."""
        if contexts is None:
            return []

        if isinstance(contexts, list):
            return contexts

        if isinstance(contexts, dict):
            documents = contexts.get("documents")
            if isinstance(documents, list):
                if documents and isinstance(documents[0], list):
                    return documents[0]
                return documents

        return [contexts]

    def _call_deepseek(self, prompt: str) -> str:
        """Call the existing DeepSeekService without adding LangChain abstractions."""
        for method_name in ("generate_answer", "generate", "ask", "chat"):
            method = getattr(self.deepseek_service, method_name, None)
            if method is None:
                continue

            response = method(prompt)
            return self._response_to_text(response)

        raise AttributeError(
            "DeepSeekService needs one of these methods: generate_answer, generate, ask, chat"
        )

    def _create_deepseek_service(self) -> Any:
        """Load the project's existing DeepSeek service without forcing a new filename."""
        candidates = (
            ("app.services.deepseek_service", "DeepSeekService"),
            ("app.services.llm_service", "DeepSeekService"),
            ("app.services.llm_service", "LLMService"),
            ("app.services.ai_service", "DeepSeekService"),
            ("app.services.chat_service", "DeepSeekService"),
        )

        for module_name, class_name in candidates:
            try:
                module = import_module(module_name)
                service_class = getattr(module, class_name)
                return service_class()
            except (ModuleNotFoundError, AttributeError):
                continue

        raise ModuleNotFoundError(
            "没有找到 DeepSeek 服务类。请检查第 6 阶段调用 DeepSeek 的文件名，"
            "然后把它加入 agent_workflow.py 的 _create_deepseek_service candidates。"
        )

    def _create_vector_service(self) -> Any:
        """Load the project's existing vector search service without forcing a new filename."""
        candidates = (
            ("app.services.vector_service", "VectorService"),
            ("app.services.vector_store_service", "VectorService"),
            ("app.services.vector_store_service", "VectorStoreService"),
            ("app.services.chroma_service", "VectorService"),
            ("app.services.chroma_service", "ChromaService"),
            ("app.services.embedding_service", "VectorService"),
            ("app.services.retrieval_service", "VectorService"),
            ("app.services.retrieval_service", "RetrievalService"),
        )

        for module_name, class_name in candidates:
            try:
                module = import_module(module_name)
                service_class = getattr(module, class_name)
                return service_class()
            except (ModuleNotFoundError, AttributeError):
                continue

        raise ModuleNotFoundError(
            "没有找到向量检索服务类。请运行 ls app/services，"
            "确认第 6 阶段 VectorService.query() 所在的文件名和类名。"
        )

    def _response_to_text(self, response: Any) -> str:
        """Normalize common DeepSeekService response shapes into plain answer text."""
        if isinstance(response, str):
            return response

        if isinstance(response, dict):
            for key in ("answer", "content", "text", "message"):
                value = response.get(key)
                if value:
                    return str(value)
            return str(response)

        return str(response)
