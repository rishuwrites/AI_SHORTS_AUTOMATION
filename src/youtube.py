import json, os
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from config import ROOT

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def upload_video(video_path, metadata, private=True):
    token_path = ROOT / "token.json"
    if not token_path.exists():
        print("YouTube upload skipped: token.json is not configured.")
        return None
    creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_path.write_text(creds.to_json(), encoding="utf-8")
    youtube = build("youtube", "v3", credentials=creds)
    body = {
        "snippet": {
            "title": metadata["title"][:100],
            "description": metadata.get("description", "")[:5000],
            "tags": metadata.get("tags", ["shorts"])[:500],
            "categoryId": os.getenv("YOUTUBE_CATEGORY_ID", "27")
        },
        "status": {
            "privacyStatus": "private" if private else "public",
            "selfDeclaredMadeForKids": False
        }
    }
    media = MediaFileUpload(str(video_path), mimetype="video/mp4", resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"YouTube upload progress: {int(status.progress() * 100)}%")
    print("Uploaded video ID:", response["id"])
    return response["id"]
