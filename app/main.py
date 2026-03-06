from fastapi import FastAPI

app = FastAPI(title="Garden Station Backend")

@app.get("/")
def read_root():
    return {"status": "Backend Orchestrator Running"}
