# Profile Storage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add SQLite storage to ai-service for storing profile_link → target_dir mappings with update timestamps and file lists.

**Architecture:** Simple SQLite database with single table. Use sqlite3 from stdlib. Storage module provides simple CRUD interface.

**Tech Stack:** Python stdlib sqlite3, ai-service FastAPI

---

### Task 1: Create storage module

**Files:**
- Create: `python/ai-service/app/storage.py`

- [ ] **Step 1: Write storage module**

```python
"""SQLite storage for profile data."""
import sqlite3
import json
import os
from datetime import datetime
from typing import Optional

DB_PATH = os.getenv("AI_SERVICE_DB_PATH", "/tmp/ai-service.db")


def init_db():
    """Initialize database and create tables."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            profile_link TEXT PRIMARY KEY,
            target_dir TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            files TEXT
        )
    """)
    conn.commit()
    conn.close()


def get_connection():
    """Get database connection."""
    return sqlite3.connect(DB_PATH)


def get_profile(profile_link: str) -> Optional[dict]:
    """Get profile by link."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(
        "SELECT profile_link, target_dir, updated_at, files FROM profiles WHERE profile_link = ?",
        (profile_link,)
    )
    row = cursor.fetchone()
    conn.close()
    
    if row is None:
        return None
    
    return {
        "profile_link": row["profile_link"],
        "target_dir": row["target_dir"],
        "updated_at": row["updated_at"],
        "files": json.loads(row["files"]) if row["files"] else []
    }


def save_profile(profile_link: str, target_dir: str, files: list[str]):
    """Save or update profile record."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO profiles (profile_link, target_dir, updated_at, files)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(profile_link) DO UPDATE SET
            target_dir = excluded.target_dir,
            updated_at = excluded.updated_at,
            files = excluded.files
    """, (profile_link, target_dir, datetime.now().isoformat(), json.dumps(files)))
    conn.commit()
    conn.close()


def get_all_profiles() -> list[dict]:
    """Get all profiles."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT profile_link, target_dir, updated_at, files FROM profiles")
    rows = cursor.fetchall()
    conn.close()
    
    return [
        {
            "profile_link": row["profile_link"],
            "target_dir": row["target_dir"],
            "updated_at": row["updated_at"],
            "files": json.loads(row["files"]) if row["files"] else []
        }
        for row in rows
    ]
```

- [ ] **Step 2: Commit**

```bash
git add python/ai-service/app/storage.py
git commit -m "feat: add SQLite storage module for profile data"
```

---

### Task 2: Integrate storage into load_user_data

**Files:**
- Modify: `python/ai-service/app/load_user_data.py`

- [ ] **Step 1: Update load_user_data.py to use storage**

```python
"""
Load user data from hemagon.com, save to files, and analyze with LLM
"""
import os
import uuid
import json
import requests
from typing import Optional
from app.read_user_data import analyze_user_data
from app.llm_client import create_llm_client, LLMClient
from app.storage import init_db, get_profile, save_profile


DEFAULT_HEMAGON_API_URL = os.getenv("HEMAGON_API_URL", "http://localhost:8000")


def load_and_analyze(
    profile_link: str,
    target_dir: Optional[str] = None,
    hemagon_api_url: str = DEFAULT_HEMAGON_API_URL,
    llm_client: Optional[LLMClient] = None
) -> dict:
    """
    Load profile from hemagon.com, save files, and analyze with LLM.
    """
    init_db()
    
    existing = get_profile(profile_link)
    if existing and target_dir is None:
        target_dir = existing["target_dir"]
    
    if target_dir is None:
        target_dir = os.path.join("/tmp", "hemagon_data", str(uuid.uuid4()))
    
    os.makedirs(target_dir, exist_ok=True)
    
    response = requests.post(
        f"{hemagon_api_url}/load_user_profile",
        json={"profile_link": profile_link, "target_dir": target_dir},
        timeout=300
    )
    response.raise_for_status()
    
    scrape_result = response.json()
    
    result = analyze_user_data(target_dir, llm_client)
    
    result["target_dir"] = target_dir
    result["files_saved"] = scrape_result.get("files_saved", [])
    
    all_files = result.get("files_saved", [])
    result_json_path = os.path.join(target_dir, "result.json")
    with open(result_json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    all_files.append("result.json")
    
    save_profile(profile_link, target_dir, all_files)
    result["files_saved"] = all_files
    
    return result
```

- [ ] **Step 2: Commit**

```bash
git add python/ai-service/app/load_user_data.py
git commit -m "feat: integrate storage into load_and_analyze"
```

---

### Task 3: Update get_existing_profile to use storage

**Files:**
- Modify: `python/ai-service/main.py`

- [ ] **Step 1: Update main.py to use storage**

Add import and update endpoint to use storage:

```python
from app.storage import init_db, get_profile

# Add at startup
init_db()

# Update get_existing_profile request model
class GetExistingProfileRequest(BaseModel):
    profile_link: str  # Instead of data_dir
```

Update the endpoint:

```python
@app.post("/get_existing_profile", response_model=AnalyzeResponse)
async def get_existing_profile(request: GetExistingProfileRequest):
    """
    Get existing profile data by profile_link. If result.json exists, return it. Otherwise analyze files.
    """
    profile = get_profile(request.profile_link)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    target_dir = profile["target_dir"]
    
    if not os.path.isdir(target_dir):
        raise HTTPException(status_code=404, detail="Directory not found")
    
    result_json_path = os.path.join(target_dir, "result.json")
    
    if os.path.isfile(result_json_path):
        with open(result_json_path, "r", encoding="utf-8") as f:
            result = json.load(f)
        return AnalyzeResponse(
            profile=ProfileDataSchema(**result.get("profile", {})),
            target_dir=result.get("target_dir", target_dir),
            files_saved=result.get("files_saved", [])
        )
    
    try:
        result = analyze_user_data_sync(target_dir)
        return AnalyzeResponse(
            profile=ProfileDataSchema(**result.get("profile", {})),
            target_dir=target_dir,
            files_saved=result.get("files_saved", [])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

- [ ] **Step 2: Commit**

```bash
git add python/ai-service/main.py
git commit -m "feat: update get_existing_profile to use storage by profile_link"
```

---

### Task 4: Add DB initialization to startup

**Files:**
- Modify: `python/ai-service/main.py`

- [ ] **Step 1: Add startup event**

```python
@app.on_event("startup")
async def startup_event():
    init_db()
```

- [ ] **Step 2: Commit**

```bash
git add python/ai-service/main.py
git commit -m "feat: add startup DB initialization"
```

---

**Plan complete.** Four tasks covering:
1. Storage module with SQLite
2. Integration into load_and_analyze
3. Update get_existing_profile endpoint
4. Startup initialization