from fastapi import FastAPI
from backend.app.routers import vehicles
from backend.app.routers import analytics

app = FastAPI(
    title="Fleet Intelligence",
    description = "Real time fleet monitoring and analytics platform",
    version="1.0.0",
)   
app.include_router(vehicles.router)
app.include_router(analytics.router)

@app.get('/')
def root():
    return{
        "message": "Fleet Intelligence API is running"
    }

@app.get("/health")
def health_check():
    return{
        "message": "healthy"
    }