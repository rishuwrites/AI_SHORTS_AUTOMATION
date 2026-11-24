import asyncio, os
from pathlib import Path
import edge_tts

def make_voice(text, output_path, language, gender):
    voice_map = {
        ("hindi", "male"): "hi-IN-MadhurNeural",
        ("hindi", "female"): "hi-IN-SwaraNeural",
        ("english", "male"): "en-US-GuyNeural",
        ("english", "female"): "en-US-JennyNeural",
        ("hinglish", "male"): "hi-IN-MadhurNeural",
        ("hinglish", "female"): "hi-IN-SwaraNeural"
    }
    voice = os.getenv("TTS_VOICE") or voice_map.get((language.lower(), gender), "hi-IN-MadhurNeural")
    async def run():
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(output_path))
    asyncio.run(run())
    return output_path
