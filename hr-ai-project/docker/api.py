from fastapi import FastAPI, UploadFile, File, Query
from typing import Optional

app = FastAPI(title="HR AI API Baseline")

@app.get("/")
def read_root():
    return {"status": "success", "message": "HR AI API is running successfully!"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/v1/models")
def list_models():
    return {
        "object": "list",
        "data": [
            {"id": "mock", "object": "model", "owned_by": "hr-team"}
        ]
    }

@app.post("/v1/resumes/parse")
async def parse_resume(
    file: UploadFile = File(...),
    model: Optional[str] = Query("mock")
):
    return {
        "filename": file.filename,
        "status": "parsed",
        "model_used": model,
        "parsed_data": {
            "name": "Sample Candidate",
            "skills": ["Python", "Docker", "FastAPI"],
            "summary": "Mock output for baseline test"
        }
    }