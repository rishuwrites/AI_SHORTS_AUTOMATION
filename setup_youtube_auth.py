"""
Run locally once:
  1. Download OAuth Desktop App credentials from Google Cloud.
  2. Save them beside this file as client_secret.json.
  3. Run: python setup_youtube_auth.py
  4. Sign in to the channel and save the generated token.json securely.
Do not commit either JSON file to GitHub.
"""
from google_auth_oauthlib.flow import InstalledAppFlow
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")
Path("token.json").write_text(creds.to_json(), encoding="utf-8")
print("Created token.json. Keep it private.")
