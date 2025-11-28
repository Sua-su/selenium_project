from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import dataset

app = FastAPI(title="Anomaly Detection Lab API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dataset.router, prefix="/api")

@app.get("/")
def root():
    return {"message": "Anomaly Detection Lab API"}
