from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api.chat import router as chat_router
from backend.app.api.projects import router as projects_router


app = FastAPI(title="AI Coding Agent")
STATIC_DIR = Path(__file__).parent / "static"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(chat_router)
app.include_router(projects_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/chat")
def chat_page():
    return FileResponse(STATIC_DIR / "chat.html")
