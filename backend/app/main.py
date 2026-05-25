from fastapi import FastAPI

from backend.app.api.projects import router as projects_router


app = FastAPI(title="AI Coding Agent")

app.include_router(projects_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
