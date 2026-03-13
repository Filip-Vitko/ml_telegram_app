import uvicorn
from fastapi import FastAPI
from enum import Enum

class ModelName(str, Enum):
    llama3 = "llama3"
    qwen3 = "qwen3"
    mistral = "mistral"

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/model/{model_name}")
def get_model_response(model_name: ModelName):
    message = ""
    return {"model": model_name.value, "message": message}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)