from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import uuid, os, io
from PIL import Image
from utils.overlay import annotate_image
from providers.llm_provider import generate_shots_with_llm

app = FastAPI(title="Storyboard API", version="1.0.0")

# serve generated assets
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

class Shot(BaseModel):
    id: int
    title: str
    framing: str
    camera_angle: str
    movement: str
    lens: str
    duration_sec: float
    notes: str

class StoryboardResponse(BaseModel):
    prompt: str
    language: str
    shots: List[Shot]
    annotated_images: List[str] = Field(default_factory=list, description="URLs of annotated images")

def _heuristic_plan(prompt: str, num_shots: int, language: str) -> List[Dict]:
    # Simple planner based on keywords
    movement = "dolly in, slow" if "دالی" in prompt or "dolly" in prompt.lower() else "pan right, slow"
    angle = "45° three-quarter" if "45" in prompt else "eye level"
    framing_cycle = ["WS","MS","CU","ECU"]
    lens_cycle = ["24mm","35mm","50mm","85mm"]

    shots = []
    for i in range(num_shots):
        shots.append({
            "id": i+1,
            "title": f"Shot {i+1}",
            "framing": framing_cycle[i % len(framing_cycle)],
            "camera_angle": angle,
            "movement": movement if i != 0 else "static",
            "lens": lens_cycle[i % len(lens_cycle)],
            "duration_sec": 3.0 if i < num_shots-1 else 4.0,
            "notes": "Keep shallow DoF; lock white balance; match eyeline."
        })
    return shots

def _caption_image(img: Image.Image) -> str:
    # Extremely light "caption": just size info; (placeholder for real vision captioning)
    return f"{img.width}x{img.height} scene, central subject likely."

@app.post("/v1/storyboard", response_model=StoryboardResponse)
async def storyboard(
    prompt: str = Form(..., description="Creative brief in fa/en"),
    shots: int = Form(3, ge=1, le=12),
    language: str = Form("fa"),
    images: List[UploadFile] = File(..., description="1..N reference frames")
):
    # Prepare working dir
    job_id = str(uuid.uuid4())[:8]
    job_dir = os.path.join("outputs", job_id)
    os.makedirs(job_dir, exist_ok=True)

    # Load images
    img_paths = []
    captions = []
    for idx, uf in enumerate(images):
        raw = await uf.read()
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        in_path = os.path.join(job_dir, f"in_{idx+1}.jpg")
        img.save(in_path, "JPEG", quality=92)
        img_paths.append(in_path)
        captions.append(_caption_image(img))

    # Try LLM provider, then fallback
    llm_shots = generate_shots_with_llm(prompt, captions, shots, language)
    plan = llm_shots if llm_shots else _heuristic_plan(prompt, shots, language)

    # Annotate each image with the corresponding shot (cycle if fewer images)
    annotated_urls = []
    for i, path in enumerate(img_paths):
        shot = plan[i % len(plan)]
        out_path = os.path.join(job_dir, f"annotated_{i+1}.jpg")
        annotate_image(path, shot, out_path)
        annotated_urls.append(f"/outputs/{job_id}/annotated_{i+1}.jpg")

    resp = {
        "prompt": prompt,
        "language": language,
        "shots": plan,
        "annotated_images": annotated_urls
    }
    return JSONResponse(resp)
