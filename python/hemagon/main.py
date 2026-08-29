"""
HEMAGON FastAPI Server
"""
from fastapi import FastAPI
from pydantic import BaseModel
from app.parse_user_profile import load_user_profile_async

app = FastAPI(title="HEMAGON API")


class LoadProfileRequest(BaseModel):
    profile_link: str
    target_dir: str


@app.post("/load_user_profile")
async def load_user_profile_endpoint(request: LoadProfileRequest):
    """Load a HEMA fighter's profile from hemagon.com"""
    result = await load_user_profile_async(request.profile_link, request.target_dir)
    return result


@app.get("/health")
async def health():
    return {"status": "ok"}