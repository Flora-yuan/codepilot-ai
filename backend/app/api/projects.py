import shutil
import uuid
import zipfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.app.core.code_loader import load_cpp_source_files


router = APIRouter(prefix="/api/projects", tags=["projects"])

UPLOAD_ROOT = Path("backend/data/uploads")


def _safe_extract_zip(zip_file: zipfile.ZipFile, target_dir: Path) -> None:
    target_dir = target_dir.resolve()

    for member in zip_file.infolist():
        member_path = (target_dir / member.filename).resolve()
        if not str(member_path).startswith(str(target_dir)):
            raise HTTPException(status_code=400, detail="Invalid zip file path")

    zip_file.extractall(target_dir)


@router.post("/upload")
async def upload_project(file: UploadFile = File(...)):
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip files are supported")

    project_id = uuid.uuid4().hex
    project_name = Path(file.filename).stem
    project_dir = UPLOAD_ROOT / project_id
    zip_path = project_dir / "source.zip"

    project_dir.mkdir(parents=True, exist_ok=True)

    try:
        with zip_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        with zipfile.ZipFile(zip_path) as zip_file:
            _safe_extract_zip(zip_file, project_dir)

        zip_path.unlink()
    except zipfile.BadZipFile as exc:
        shutil.rmtree(project_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail="Invalid zip file") from exc

    return {
        "project_id": project_id,
        "project_name": project_name,
        "message": "Project uploaded successfully",
    }


@router.get("/{project_id}/files")
def list_project_files(project_id: str):
    project_dir = UPLOAD_ROOT / project_id

    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="Project not found")

    source_files = load_cpp_source_files(project_dir)

    return {
        "project_id": project_id,
        "file_count": len(source_files),
        "files": [
            {
                "path": source_file.relative_path,
                "line_count": source_file.line_count,
                "size": source_file.size,
            }
            for source_file in source_files
        ],
    }
