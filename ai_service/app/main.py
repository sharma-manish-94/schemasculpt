from fastapi import FastAPI
from app.api import endpoints

app = FastAPI(title="SchemaSculpt AI Service")

app.include_router(endpoints.router)

@app.get("/")
def read_root():
    return {"message": "SchemaSculpt AI Service is running"}