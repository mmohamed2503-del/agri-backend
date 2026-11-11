import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import crops, weather, environment, data, grid, dashboard

app = FastAPI(
    title="Field Shift API",
    description="Nile Delta crop suitability and rotation explorer — NASA Space Apps",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(crops.router)
app.include_router(weather.router)
app.include_router(environment.router)
app.include_router(data.router)
app.include_router(grid.router)
app.include_router(dashboard.router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"message": "Field Shift API is running", "docs": "/docs"}
