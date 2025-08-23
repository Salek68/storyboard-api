# Storyboard API (Python + FastAPI)

Send 1..N reference photos (`images[]`) plus a text brief (`prompt`) and get back:
1) A structured **shot list** (JSON)
2) **Annotated storyboard overlays** on your own photos (arrows, framing, notes)

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate  # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Example cURL
```bash
curl -X POST "http://127.0.0.1:8000/v1/storyboard"   -F "prompt=یک ویدیو موشن پر از عمق میدان. حرکت دوربین دالی-این؛ تمرکز روی آیفون روی میز."   -F "shots=4"   -F "language=fa"   -F "images=@samples/desk.jpg"   -F "images=@samples/room.jpg"
```

Open the docs at: http://127.0.0.1:8000/docs

> By default it uses a heuristic planner (no API keys required).  
> To plug in an LLM later, fill in `providers/llm_provider.py` and set env vars.
