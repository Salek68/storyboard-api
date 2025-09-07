from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import JSONResponse
import shutil, os, uuid
from utils.overlay import annotate_image

app = FastAPI()

OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.post("/generate-storyboard")
async def generate_storyboard(
    files: list[UploadFile],
    prompt: str = Form(...)
):
    session_id = str(uuid.uuid4())
    session_path = os.path.join(OUTPUT_DIR, session_id)
    os.makedirs(session_path, exist_ok=True)

    shots = []
    annotated_images = []

    for idx, file in enumerate(files):
        file_path = os.path.join(session_path, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        annotated_path = os.path.join(session_path, f"annotated_{idx+1}.png")
        annotate_image(file_path, f"Plan {idx+1}: {prompt}", annotated_path)

        shots.append({
            "id": idx+1,
            "title": f"Plan {idx+1}",
            "movement": "Static",
            "angle": "Eye level",
            "duration_sec": 3
        })
        annotated_images.append(annotated_path)

    return JSONResponse({
        "prompt": prompt,
        "shots": shots,
        "annotated_images": annotated_images
    })
