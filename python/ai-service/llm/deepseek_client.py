"""
DeepSeek LLM Client
"""
import os
import json
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.base_url = base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.completion_path = os.getenv("DEEPSEEK_COMPLETION_PATH", "/chat/completion")
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable not set")
    
    def chat(self, system_prompt: str, user_prompt: str, model: str = "DeepSeek-Coder") -> dict:
        """Send chat request to DeepSeek and return parsed JSON response."""
        url = f"{self.base_url}{self.completion_path}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }
        
        logger.debug("LLM request to %s: model=%s", url, model)
        
        response = requests.post(url, headers=headers, json=payload, timeout=120)

        logger.debug("LLM response: %s", response.json())
        response.raise_for_status()
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        logger.debug("LLM raw response: %s", content)
        
        try:
            parsed = json.loads(content)
            logger.debug("LLM parsed response: %s", parsed)
            return parsed
        except json.JSONDecodeError:
            logger.error("Failed to parse LLM response as JSON: %s", content)
            return {"error": "Failed to parse JSON", "raw_content": content}


def create_llm_client() -> LLMClient:
    """Factory function to create LLM client."""
    return LLMClient()