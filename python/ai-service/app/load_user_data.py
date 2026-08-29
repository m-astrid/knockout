"""
Load user data from hemagon.com, save to files, and analyze with LLM
"""
import os
import uuid
import json
import requests
from typing import Optional
from dataclasses import dataclass
from app.read_user_data import analyze_user_data
from llm import create_llm_client, LLMClient
from store import init_db, get_profile, save_profile


@dataclass
class LoadAndAnalyzeResult:
    profile: dict
    target_dir: str
    files_saved: list[str]


DEFAULT_HEMAGON_API_URL = os.getenv("HEMAGON_API_URL", "http://localhost:8000")


def load_and_analyze(
    profile_link: str,
    target_dir: Optional[str] = None,
    hemagon_api_url: str = DEFAULT_HEMAGON_API_URL,
    llm_client: Optional[LLMClient] = None
) -> LoadAndAnalyzeResult:
    """
    Load profile from hemagon.com, save files, and analyze with LLM.
    
    Args:
        profile_link: URL to hemagon profile (e.g., 'https://hemagon.com/users/nekrasova')
        target_dir: Directory to save files (auto-generated if not provided)
        hemagon_api_url: URL of hemagon API service
        llm_client: Optional LLM client
    
    Returns:
        LoadAndAnalyzeResult with analysis result and file paths
    """
    
    existing = get_profile(profile_link)
    if existing and target_dir is None:
        target_dir = existing.target_dir
    
    if target_dir is None:
        target_dir = os.path.join("/tmp", "hemagon_data", profile_link.split("/")[-1])
    
    os.makedirs(target_dir, exist_ok=True)
    
    response = requests.post(
        f"{hemagon_api_url}/load_user_profile",
        json={"profile_link": profile_link, "target_dir": target_dir},
        timeout=300
    )
    response.raise_for_status()
    
    scrape_result = response.json()
    
    files_saved = scrape_result.get("files_saved", [])

    save_profile(profile_link, target_dir, files_saved)
    
    result = analyze_user_data(target_dir, llm_client)
    
    result_json_path = os.path.join(target_dir, "result.json")
    try:
        with open(vk_filepath, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        files_saved.append("result.json")
    except Exception as e:
        print(f"Failed to write result.json: {e}")

    save_profile(profile_link, target_dir, files_saved)
    
    return LoadAndAnalyzeResult(
        profile=result if isinstance(result, dict) else result.profile,
        target_dir=target_dir,
        files_saved=files_saved
    )


def load_and_analyze_sync(
    profile_link: str,
    target_dir: Optional[str] = None,
    hemagon_api_url: str = DEFAULT_HEMAGON_API_URL
) -> LoadAndAnalyzeResult:
    """Synchronous wrapper for load_and_analyze."""
    return load_and_analyze(profile_link, target_dir, hemagon_api_url)