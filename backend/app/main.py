from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException
from sqlmodel import SQLModel, Field, Session, create_engine, select


# Database setup
sqlite_file_name = "nudilog.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, echo=True)


# Sighting Model
class Sighting(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    seen_at: datetime
    location_name: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    depth_m: Optional[float] = None
    habitat: Optional[str] = None


# Sighting Schema for POST (without id)
class SightingCreate(SQLModel):
    seen_at: datetime
    location_name: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    depth_m: Optional[float] = None
    habitat: Optional[str] = None


# Sighting Schema for GET (with id)
class SightingRead(SQLModel):
    id: int
    seen_at: datetime
    location_name: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    depth_m: Optional[float] = None
    habitat: Optional[str] = None


# FastAPI app
app = FastAPI()


@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)


@app.post("/sightings", response_model=SightingRead)
def create_sighting(sighting: SightingCreate):
    with Session(engine) as session:
        db_sighting = Sighting(**sighting.model_dump())
        session.add(db_sighting)
        session.commit()
        session.refresh(db_sighting)
        return db_sighting


@app.get("/sightings/{sighting_id}", response_model=SightingRead)
def get_sighting(sighting_id: int):
    with Session(engine) as session:
        sighting = session.get(Sighting, sighting_id)
        if not sighting:
            raise HTTPException(status_code=404, detail="Sighting not found")
        return sighting


@app.get("/sightings", response_model=list[SightingRead])
def get_all_sightings():
    with Session(engine) as session:
        statement = select(Sighting)
        sightings = session.exec(statement).all()
        return sightings

