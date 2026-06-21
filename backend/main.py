import os
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import asyncio
import tempfile
import sys
import multiprocessing

# Add parent dir to path so we can import the extractor script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from convert_full import convert_pdf_to_excel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global store for progress
extraction_progress = {}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), background_tasks: BackgroundTasks = BackgroundTasks()):
    # Save uploaded file
    file_id = "job_" + str(int(asyncio.get_event_loop().time()))
    temp_pdf = f"/tmp/{file_id}.pdf"
    
    with open(temp_pdf, "wb") as f:
        f.write(await file.read())
        
    extraction_progress[file_id] = {
        "status": "starting",
        "progress": 0,
        "message": "File uploaded successfully.",
        "download_url": None
    }
    
    background_tasks.add_task(run_extraction, temp_pdf, file_id)
    return {"job_id": file_id}

@app.get("/api/progress/{job_id}")
async def get_progress(job_id: str):
    async def event_generator():
        while True:
            if job_id in extraction_progress:
                state = extraction_progress[job_id]
                yield {"data": state}
                if state["status"] in ["completed", "error"]:
                    break
            else:
                yield {"data": {"status": "error", "message": "Job not found."}}
                break
            await asyncio.sleep(1)
            
    return EventSourceResponse(event_generator())

@app.get("/api/download/{job_id}")
async def download_file(job_id: str):
    if job_id in extraction_progress and extraction_progress[job_id]["status"] == "completed":
        excel_path = extraction_progress[job_id]["download_url"]
        return FileResponse(path=excel_path, filename="Voter_List.xlsx", media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    return {"error": "File not ready or not found."}

def run_extraction(pdf_path: str, job_id: str):
    try:
        extraction_progress[job_id]["status"] = "processing"
        extraction_progress[job_id]["message"] = "Initializing perfect quality text extraction..."
        
        output_excel = f"/tmp/{job_id}_output.xlsx"
        
        def progress_updater(percent, message):
            extraction_progress[job_id]["progress"] = percent
            extraction_progress[job_id]["message"] = message
            
        # This function directly extracts perfect text from the embedded Gautami font (no OCR required)
        convert_pdf_to_excel(pdf_path, output_excel, progress_callback=progress_updater)
            
        extraction_progress[job_id]["status"] = "completed"
        extraction_progress[job_id]["progress"] = 100
        extraction_progress[job_id]["message"] = "Extraction complete!"
        extraction_progress[job_id]["download_url"] = output_excel
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        extraction_progress[job_id]["status"] = "error"
        extraction_progress[job_id]["message"] = f"Error during extraction: {str(e)}"
