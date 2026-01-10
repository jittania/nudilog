from datetime import datetime
from typing import Optional, List
import os
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from sqlmodel import SQLModel, Field, Session, create_engine, select, Relationship
from sqlalchemy.orm import selectinload


# Database setup
sqlite_file_name = "nudilog.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, echo=True)

# Create uploads directory if it doesn't exist
UPLOADS_DIR = "uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)


# DiveEntry Model (represents a dive)
class DiveEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    dive_date: datetime
    location_name: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    av_depth_m: Optional[float] = None
    av_water_temp_c: Optional[float] = None
    habitat: Optional[str] = None
    sightings: list["Sighting"] = Relationship(back_populates="dive_entry")


# DiveEntry Schema for POST (without id)
class DiveEntryCreate(SQLModel):
    dive_date: datetime
    location_name: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    av_depth_m: Optional[float] = None
    av_water_temp_c: Optional[float] = None
    habitat: Optional[str] = None


# DiveEntry Schema for GET (with id)
class DiveEntryRead(SQLModel):
    id: int
    dive_date: datetime
    location_name: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    av_depth_m: Optional[float] = None
    av_water_temp_c: Optional[float] = None
    habitat: Optional[str] = None
    sightings: List["SightingRead"] = []


# Sighting Model (represents an individual sighting/photo within a dive)
class Sighting(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    dive_entry_id: int = Field(foreign_key="diveentry.id")
    filename: str
    file_path: str
    dive_entry: DiveEntry = Relationship(back_populates="sightings")


# Sighting Schema for POST (without id)
class SightingCreate(SQLModel):
    dive_entry_id: int
    filename: str
    file_path: str


# Sighting Schema for GET (with id)
class SightingRead(SQLModel):
    id: int
    dive_entry_id: int
    filename: str
    file_path: str


# Rebuild models to resolve forward references
DiveEntryRead.model_rebuild()


# FastAPI app
app = FastAPI()


@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)


@app.post("/dive-entries", response_model=DiveEntryRead)
def create_dive_entry(dive_entry: DiveEntryCreate):
    with Session(engine) as session:
        db_dive_entry = DiveEntry(**dive_entry.model_dump())
        session.add(db_dive_entry)
        session.commit()
        session.refresh(db_dive_entry)
        # Load sightings relationship
        statement = select(DiveEntry).options(selectinload(DiveEntry.sightings)).where(DiveEntry.id == db_dive_entry.id)
        db_dive_entry = session.exec(statement).first()
        return db_dive_entry


@app.get("/dive-entries/{dive_entry_id}", response_model=DiveEntryRead)
def get_dive_entry(dive_entry_id: int):
    with Session(engine) as session:
        statement = select(DiveEntry).options(selectinload(DiveEntry.sightings)).where(DiveEntry.id == dive_entry_id)
        dive_entry = session.exec(statement).first()
        if not dive_entry:
            raise HTTPException(status_code=404, detail="Dive entry not found")
        return dive_entry


@app.get("/dive-entries", response_model=list[DiveEntryRead])
def get_all_dive_entries():
    with Session(engine) as session:
        statement = select(DiveEntry).options(selectinload(DiveEntry.sightings))
        dive_entries = session.exec(statement).all()
        return dive_entries


@app.post("/sightings", response_model=SightingRead)
async def upload_sighting(
    dive_entry_id: int = Form(...),
    file: UploadFile = File(...)
):
    # Verify dive entry exists
    with Session(engine) as session:
        dive_entry = session.get(DiveEntry, dive_entry_id)
        if not dive_entry:
            raise HTTPException(status_code=404, detail="Dive entry not found")

    # Save file to disk
    file_path = os.path.join(UPLOADS_DIR, file.filename)
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Save sighting record to database
    with Session(engine) as session:
        db_sighting = Sighting(
            dive_entry_id=dive_entry_id,
            filename=file.filename,
            file_path=file_path
        )
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


@app.get("/dive-entries/{dive_entry_id}/sightings", response_model=list[SightingRead])
def get_dive_entry_sightings(dive_entry_id: int):
    with Session(engine) as session:
        # Verify dive entry exists
        dive_entry = session.get(DiveEntry, dive_entry_id)
        if not dive_entry:
            raise HTTPException(status_code=404, detail="Dive entry not found")

        # Get all sightings for this dive entry
        statement = select(Sighting).where(Sighting.dive_entry_id == dive_entry_id)
        sightings = session.exec(statement).all()
        return sightings
