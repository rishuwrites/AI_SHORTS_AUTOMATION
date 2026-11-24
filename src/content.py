import json
import os
import re
import requests
from pathlib import Path
from config import ROOT

HISTORY = ROOT / "topic_history.txt"

def _history():
    if not HISTORY.exists():
        return []
    return HISTORY.read_text(encoding="utf-8").splitlines()[-100:]

def _extract_json(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("AI response did not contain a JSON object")
    return json.loads(text[start:end+1])

def generate_content(config):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY. Add it to GitHub Actions secrets or your local .env.")
    model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    prompt = f"""
Create ONE original, factual, engaging YouTube Short.
Niche: {config['channel_niche']}
Language: {config['language']}
Target duration: {config['duration_seconds']} seconds.
Avoid these previously used topics: {_history()}

Return ONLY valid JSON with this exact structure:
{{
 "topic": "short topic",
 "title": "catchy title, ideally under 65 characters",
 "description": "2-3 sentence description and relevant hashtags",
 "tags": ["tag1","tag2"],
 "narration": "complete spoken script in {config['language']}, about {config['duration_seconds']} seconds",
 "scenes": [
   {{"caption":"very short on-screen caption","visual_query":"clear searchable visual description"}}
 ]
}}
Use exactly {config['scene_count']} scenes. The narration must be original, coherent, fact-checked to the best of your knowledge, and avoid unsupported sensational claims. Do not include markdown.
"""
    response = requests.post(url, json={
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.8, "responseMimeType": "application/json"}
    }, timeout=90)
    response.raise_for_status()
    body = response.json()
    try:
        raw = body["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"Unexpected Gemini response: {body}") from exc
    data = _extract_json(raw)
    required = ("topic", "title", "description", "narration", "scenes")
    if any(not data.get(k) for k in required):
        raise ValueError("AI response is missing one or more required fields")
    if len(data["scenes"]) < 2:
        raise ValueError("AI must return at least two scenes")
    return data

def save_topic(topic):
    old = _history()
    old.append(topic.replace("\n", " ").strip())
    HISTORY.write_text("\n".join(old[-100:]) + "\n", encoding="utf-8")
