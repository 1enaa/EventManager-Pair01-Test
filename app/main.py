from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from .routers import events, participants, registrations


app = FastAPI(
    title="Event Manager API",
    description="A teaching project for Git, Docker and CI/CD",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
Base.metadata.create_all(bind=engine)


app.include_router(events.router)
app.include_router(participants.router)
app.include_router(registrations.router)

@app.get("/")
def root():
    return {
        "message": "Welcome to Event Manager API"
    }