import subprocess, json, math
from pathlib import Path

def run(cmd):
    print("RUN:", " ".join(map(str, cmd)))
    subprocess.run(list(map(str, cmd)), check=True)

def probe_duration(path):
    result = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path)
    ], text=True)
    return float(result.strip())

def render_video(images, audio, output, work_dir, target_seconds):
    audio_len = probe_duration(audio)
    duration = max(10.0, min(float(target_seconds), audio_len + 0.5))
    per_scene = duration / len(images)
    segments = []
    for i, image in enumerate(images):
        seg = work_dir / f"segment_{i:02d}.mp4"
        run(["ffmpeg", "-y", "-loop", "1", "-i", image, "-t", f"{per_scene:.3f}",
             "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,format=yuv420p",
             "-r", "30", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "24",
             "-pix_fmt", "yuv420p", seg])
        segments.append(seg)
    concat = work_dir / "concat.txt"
    concat.write_text("".join(f"file '{p.as_posix()}'\n" for p in segments), encoding="utf-8")
    silent = work_dir / "silent.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat, "-c", "copy", silent])
    run(["ffmpeg", "-y", "-i", silent, "-i", audio, "-map", "0:v:0", "-map", "1:a:0",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest",
         "-movflags", "+faststart", output])
    return output
