
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.routers import vehicles
from backend.app.routers import analytics

app = FastAPI(
    title="Fleet Intelligence API",
    description="Real-time fleet monitoring and analytics platform",
    version="1.0.0"
)

# Allow our React frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vehicles.router)
app.include_router(analytics.router)

@app.get("/")
def root():
    return {"message": "Fleet Intelligence API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
