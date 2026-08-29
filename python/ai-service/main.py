"""
EXPLOIT AI Service - FastAPI Server
"""
import os
import json
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.load_user_data import load_and_analyze_sync
from app.read_user_data import analyze_user_data_sync
from store import init_db, get_profile

app = FastAPI(title="EXPLOIT AI Service")

HEMAGON_SCRAPPER_URL = os.getenv("HEMAGON_SCRAPPER_URL", "http://localhost:8000")


class WeaponSchema(BaseModel):
    name: str
    rank: Optional[int] = None
    rating: Optional[int] = None
    events: Optional[int] = None
    fights: Optional[int] = None
    win_percent: Optional[int] = None


class FightSchema(BaseModel):
    opponent: str
    club: Optional[str] = None
    user_score: int
    opponent_score: int
    result: str
    tournament: str
    stage: Optional[str] = None
    date: str
    weapon: str


class TournamentSchema(BaseModel):
    name: str
    url: Optional[str] = None
    slug: Optional[str] = None
    category: Optional[str] = None
    vk_link: Optional[str] = None


class SummarySchema(BaseModel):
    events: Optional[int] = None
    categories: Optional[int] = None
    fights: Optional[int] = None


class ProfileDataSchema(BaseModel):
    name: Optional[str] = None
    club: Optional[str] = None
    country: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[SummarySchema] = None
    weapons: list[WeaponSchema] = []
    fights: list[FightSchema] = []
    tournaments: list[TournamentSchema] = []


class AnalyzeResponse(BaseModel):
    profile: ProfileDataSchema


class AnalyzeProfileRequest(BaseModel):
    profile_link: str


class AnalyzeExistingRequest(BaseModel):
    profile_link: str


@app.post("/load_or_update_profile", response_model=AnalyzeResponse)
async def load_or_update_profile(request: AnalyzeProfileRequest):
    """
    Load profile from hemagon.com, save files, and analyze with LLM.
    """
    try:
        result = load_and_analyze_sync(
            profile_link=request.profile_link,
            hemagon_api_url=HEMAGON_SCRAPPER_URL
        )
        return AnalyzeResponse(
            profile=ProfileDataSchema(**result.profile)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/get_existing_profile", response_model=AnalyzeResponse)
async def get_existing_profile(request: AnalyzeExistingRequest):
    """
    Get existing profile data by profile_link. If result.json exists, return it. Otherwise analyze files.
    """
    profile = get_profile(request.profile_link)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    target_dir = profile.target_dir
    
    if not os.path.isdir(target_dir):
        raise HTTPException(status_code=404, detail="Directory not found")
    
    result_json_path = os.path.join(target_dir, "result.json")
    
    if os.path.isfile(result_json_path):
        with open(result_json_path, "r", encoding="utf-8") as f:
            result = json.load(f)
        
        profile_data = result.get("profile", result)
        
        return AnalyzeResponse(
            profile=ProfileDataSchema(**profile_data)
        )

    result = analyze_user_data_sync(target_dir)
    return AnalyzeResponse(
        profile=ProfileDataSchema(**result.profile)
    )


@app.on_event("startup")
async def startup_event():
    init_db()


@app.get("/health")
async def health():
    return {"status": "ok"}