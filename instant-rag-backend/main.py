from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import project_router, chat_router, email_router, auth_router
from models.database import init_db
import run

app = FastAPI(
    title="Instant-RAG API",
    description="Backend API for Instant-RAG application",
    version="0.1.0"
)

# Make config available as a global variable
config = run.config

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(project_router, prefix="/project", tags=["project"])
app.include_router(chat_router, prefix="/chat", tags=["chat"])
app.include_router(email_router, prefix="/email", tags=["email"])

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.get("/")
async def root():
    return {"message": "Welcome to Instant-RAG API"}
