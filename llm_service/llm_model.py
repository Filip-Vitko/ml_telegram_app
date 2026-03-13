import os
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")

app = FastAPI()

class ModelRequest(BaseModel):
    model: str
    prompt: str
    # temperature: float = 0.7
    # max_tokens: int = 100
    # top_p: float = 1.0
    # frequency_penalty: float = 0.0
    # presence_penalty: float = 0.0
    # stop: list[str] = []
    # stream: bool = False

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/models")
async def models():
    try:
        async with httpx.AsyncClient(base_url=OLLAMA_BASE_URL) as client:
            resp = await client.get("/api/ps")
            resp.raise_for_status()
            data = resp.json()
            models = [model["name"] for model in data.get("models", [])]
            return {"models": models}
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Ollama request failed: {e}")

@app.post("/generate")
async def generate(request: ModelRequest):
    timeout = httpx.Timeout(connect=10.0, read=300.0, write=30.0, pool=10.0)
    
    try:
        async with httpx.AsyncClient(base_url=OLLAMA_BASE_URL, timeout=timeout) as client:
            resp = await client.post(
                "/api/generate", 
            json={
                "model": request.model,
                "prompt": request.prompt,
                "stream": False,
            },
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Ollama request failed: {e}")