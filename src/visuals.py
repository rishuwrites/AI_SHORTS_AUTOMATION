import os, textwrap, requests
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from config import ROOT
from deepai import DeepAIImageGenerator, DeepAIUnavailableError

W, H = 1080, 1920

def get_font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"
    ]
    for p in candidates:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def fetch_pexels(query, index):
    key = os.getenv("PEXELS_API_KEY")
    if not key:
        return None
    try:
        r = requests.get("https://api.pexels.com/v1/search",
            headers={"Authorization": key},
            params={"query": query, "per_page": 8, "orientation": "portrait"},
            timeout=30)
        r.raise_for_status()
        photos = r.json().get("photos", [])
        if not photos:
            return None
        photo = photos[index % len(photos)]
        img_url = photo["src"].get("large2x") or photo["src"]["large"]
        img = requests.get(img_url, timeout=30)
        img.raise_for_status()
        return Image.open(BytesIO(img.content)).convert("RGB")
    except Exception as e:
        print(f"Pexels lookup failed; using generated background: {e}")
        return None

def cover_crop(img):
    ratio = max(W / img.width, H / img.height)
    img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.Resampling.LANCZOS)
    left = (img.width - W) // 2
    top = (img.height - H) // 2
    return img.crop((left, top, left + W, top + H))

def gradient_background(seed):
    import random
    random.seed(seed)
    c1 = tuple(random.randint(8, 55) for _ in range(3))
    c2 = tuple(random.randint(50, 115) for _ in range(3))
    img = Image.new("RGB", (W, H))
    pix = img.load()
    for y in range(H):
        t = y / H
        c = tuple(int(c1[i] * (1-t) + c2[i] * t) for i in range(3))
        for x in range(W):
            pix[x, y] = c
    return img.filter(ImageFilter.GaussianBlur(1))

def draw_caption(img, caption, title=None):
    img = img.convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0,0,0,0))
    d = ImageDraw.Draw(overlay)
    d.rectangle((0, 0, W, 175), fill=(0,0,0,90))
    d.rectangle((0, 1320, W, H), fill=(0,0,0,175))
    if title:
        f = get_font(43, True)
        d.text((65, 55), title[:55], font=f, fill="white", stroke_width=2, stroke_fill=(0,0,0,180))
    f = get_font(66, True)
    lines = textwrap.wrap(caption, width=23)[:3]
    y = 1430 - (len(lines)-1)*48
    for line in lines:
        bbox = d.textbbox((0,0), line, font=f, stroke_width=3)
        x = (W - (bbox[2]-bbox[0])) // 2
        d.text((x, y), line, font=f, fill="white", stroke_width=4, stroke_fill=(0,0,0,220))
        y += 105
    return Image.alpha_composite(img, overlay).convert("RGB")

def create_scene_images(scenes, title, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    generator = DeepAIImageGenerator()
    try:
        for i, scene in enumerate(scenes):
            query = scene.get("visual_query", title)
            img = None
            if generator:
                prompt = (
                    f"{query}. Portrait 9:16 composition, cinematic visual "
                    "for a short-form video, no text or lettering."
                )
                try:
                    img = generator.generate(prompt)
                except DeepAIUnavailableError as exc:
                    print(f"DeepAI unavailable; using image fallback: {exc}")
                    generator.close()
                    generator = None
            if img is None:
                img = fetch_pexels(query, i)
            if img is None:
                img = gradient_background(i + sum(map(ord, title)))
                d = ImageDraw.Draw(img)
                d.ellipse((120+i*35, 350, 900-i*20, 1150), outline=(220,220,240), width=8)
                d.ellipse((250, 500+i*15, 830, 1080), outline=(180,200,230), width=5)
            img = cover_crop(img)
            img = draw_caption(img, scene.get("caption", ""), title if i == 0 else None)
            p = out_dir / f"scene_{i:02d}.jpg"
            img.save(p, quality=90)
            paths.append(p)
    finally:
        if generator:
            generator.close()
    return paths
