# AI Shorts Automation

Automatically creates one vertical YouTube Short per scheduled run using:
- Gemini API for topic/script generation
- Edge TTS for narration
- Pexels API for optional stock visuals (falls back to generated graphic backgrounds)
- Pillow for caption overlays
- FFmpeg for MP4 rendering
- YouTube Data API for optional upload

Default settings: Hindi, male voice, interesting facts and mysteries, 55 seconds, private upload.

## 1. Requirements

- GitHub account and repository
- Gemini API key
- Optional Pexels API key for stock images
- FFmpeg (GitHub Actions installs it automatically)
- YouTube OAuth Desktop App credentials if you want automatic uploads

## 2. Configure the project

Copy `config.example.json` to `config.json` and customize it. `config.json` is ignored by Git.

For local testing, create `.env`:
```
GEMINI_API_KEY=your_gemini_api_key
PEXELS_API_KEY=your_pexels_api_key
```
Install and run:
```
pip install -r requirements.txt
sudo apt-get install ffmpeg
python src/main.py
```
On Windows, install FFmpeg and add it to PATH. Edge TTS requires internet access.

## 3. Enable YouTube upload

1. Open Google Cloud Console and create/select a project.
2. Enable **YouTube Data API v3**.
3. Configure the OAuth consent screen and add your Google account as a test user if the app is in Testing.
4. Create an OAuth client ID of type **Desktop app** and download its JSON.
5. Save it locally as `client_secret.json`.
6. Run `pip install -r requirements.txt`, then `python setup_youtube_auth.py`.
7. Complete Google sign-in for the correct YouTube channel. This creates `token.json`.
8. In GitHub repository Settings → Secrets and variables → Actions, add:
   - `GEMINI_API_KEY` (required)
   - `PEXELS_API_KEY` (optional)
   - `YOUTUBE_CLIENT_SECRETS_JSON` (contents of client_secret.json; optional for this workflow's current uploader)
   - `YOUTUBE_TOKEN_JSON` (contents of token.json; required for upload)

Never commit API keys, client_secret.json or token.json. The OAuth token grants access to your channel; protect it like a password.

**Note:** YouTube API projects may be subject to audit/verification restrictions. Newly created or unverified API projects can have upload visibility restrictions. Check the current YouTube API compliance guidance in Google Cloud/YouTube documentation.

## 4. Run on GitHub Actions

1. Create a GitHub repository (private is fine).
2. Upload all project files.
3. Add the GitHub Actions secrets listed above.
4. Open Actions → Daily AI Short → Run workflow for a manual test.
5. The workflow is scheduled daily at 19:00 India time (13:30 UTC).
6. The workflow artifact contains the generated MP4 and metadata.

The workflow defaults to **private uploads**. Test the output before changing `UPLOAD_PRIVATELY` to `false` in the workflow. You can also change `upload_privately` in config.json for local runs.

## 5. Customize

Edit `config.example.json` and copy it to `config.json` for local runs:
- `channel_niche`
- `language`: Hindi, English or Hinglish
- `voice`: male or female
- `duration_seconds`
- `scene_count`

For GitHub Actions, edit the environment values in `.github/workflows/daily-video.yml`.

## 6. Important limitations

- Gemini and Pexels free quotas/terms can change; a valid key and available quota are required.
- Edge TTS is a community Python interface to Microsoft Edge's online TTS service, not a guaranteed commercial SLA. Review the service terms before relying on it commercially.
- Pexels visuals are stock photos, not AI-generated moving footage. The project animates them into a vertical video.
- The script asks the model to avoid repeated topics, but topic history is limited to the checked-out repository state. To persist topic history between GitHub runs, enable repository write permissions and commit the history, or store it externally. This starter workflow does not commit generated history.
- Always review factual claims, copyright/licensing, music rights, and YouTube monetization policies. Do not mass-produce repetitive or low-value videos.
- The project does not add background music by default, avoiding copyright risk.
- GitHub scheduled runs can be delayed and free runner quotas/limits apply.
