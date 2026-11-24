import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load_config():
    path = ROOT / "config.json"
    example = ROOT / "config.example.json"
    if not path.exists():
        path.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
    data = json.loads(path.read_text(encoding="utf-8"))
    data["channel_niche"] = os.getenv("CHANNEL_NICHE", data.get("channel_niche", "Interesting facts and mysteries"))
    data["language"] = os.getenv("VIDEO_LANGUAGE", data.get("language", "Hindi"))
    data["voice"] = os.getenv("VOICE_GENDER", data.get("voice", "male")).lower()
    data["duration_seconds"] = int(os.getenv("VIDEO_DURATION", data.get("duration_seconds", 55)))
    data["scene_count"] = int(data.get("scene_count", 6))
    data["upload_privately"] = os.getenv("UPLOAD_PRIVATELY", str(data.get("upload_privately", True))).lower() == "true"
    return data
