import json, os, sys, traceback
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from config import ROOT, load_config
from content import generate_content, save_topic
from visuals import create_scene_images
from voice import make_voice
from video import render_video
from youtube import upload_video

def main():
    load_dotenv(ROOT / ".env")
    config = load_config()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    work = ROOT / "work" / stamp
    out = ROOT / "output"
    work.mkdir(parents=True, exist_ok=True)
    out.mkdir(exist_ok=True)

    print("Generating topic and script...")
    content = generate_content(config)
    (work / "content.json").write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")
    save_topic(content["topic"])

    print("Generating voiceover...")
    audio = work / "voice.mp3"
    make_voice(content["narration"], audio, config["language"], config["voice"])

    print("Generating scene visuals...")
    images = create_scene_images(content["scenes"], content["title"], work / "scenes")

    print("Rendering vertical video...")
    video = out / f"short_{stamp}.mp4"
    render_video(images, audio, video, work, config["duration_seconds"])

    metadata = {
        "title": content["title"],
        "description": content["description"] + "\n\n#Shorts",
        "tags": list(dict.fromkeys(content.get("tags", []) + config.get("default_tags", []) + ["Shorts"]))
    }
    (out / f"metadata_{stamp}.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Checking final video...")
    if not video.exists() or video.stat().st_size < 100_000:
        raise RuntimeError("Rendered video is missing or unexpectedly small.")
    video_id = upload_video(video, metadata, private=config["upload_privately"])
    if video_id:
        (out / f"youtube_{stamp}.txt").write_text(f"https://youtube.com/shorts/{video_id}\n", encoding="utf-8")
    print("SUCCESS:", video)
    print("Upload:", video_id or "Skipped (configure YouTube OAuth secrets)")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
