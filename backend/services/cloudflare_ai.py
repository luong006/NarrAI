import os
import re
import requests
import urllib.parse
import io

from typing import Optional, Tuple

try:
    from PIL import Image, ImageOps, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    Image = None
    ImageOps = None
    ImageDraw = None
    ImageFont = None

# Local persistent disk cache for rendered panels
CACHE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "comic_cache"))
os.makedirs(CACHE_DIR, exist_ok=True)

# Model fallback chain: fastest first, then higher quality
CF_MODELS = [
    "@cf/bytedance/stable-diffusion-xl-lightning",
    "@cf/lykon/dreamshaper-8-lcm",
    "@cf/stabilityai/stable-diffusion-xl-base-1.0",
]

# Universal Base Negative Prompt: Banning colors, photorealism, Western comics, speech bubbles, and text/watermarks
BASE_NEGATIVE_PROMPT = (
    "color, colorful, vibrant, saturated, hue, tint, red, blue, green, yellow, pink, purple, "
    "photorealistic, photograph, photo, realistic, 3d render, CGI, digital painting, oil painting, "
    "watercolor, warm skin tones, western comic, american comic book style, superhero art style, "
    "heavy crosshatching, grunge, text, watermark, signature, font, letters, speech bubble, "
    "dialog balloon, bad anatomy, deformed hands, extra fingers, missing fingers, mutated limbs, "
    "distorted face, blurry, low resolution, messy draft, sketch lines"
)

# Modern School Exclusions: Banning historical robes, hanfu, kimono, armor, swords, palaces, and busy streets/cars
MODERN_SCHOOL_EXCLUSIONS = (
    "historical clothing, ancient robes, hanfu, kimono, yukata, martial arts costume, "
    "huyền bào, armor, knight armor, fantasy robes, cape, sword, blade, magical aura, "
    "supernatural glow, ancient temple, palace, castle, dungeon, battlefield, "
    "busy highway, traffic, moving cars, outdoor street, city avenue"
)

# Vietnamese Canonical Exclusions: Master negative against Hanfu, Kimono, Hanbok, Samurai, Ninja for cultural purity
VIETNAMESE_CANONICAL_NEGATIVE_PROMPT = (
    "hanfu, kimono, yukata, hanbok, samurai, samurai armor, ninja, katana, geisha, "
    "qing queue, pigtail hairstyle, chinese traditional clothing, japanese traditional clothing, "
    "korean traditional clothing, tangzhuang, cheongsam, qipao"
)

def get_master_negative_prompt(
    genre: str = "school",
    cultural_tier: Optional[int] = None,
    narrative_mode: Optional[str] = None
) -> str:
    """
    Returns the master negative prompt combining base exclusions with genre-specific
    and cultural tier exclusions.
    - If cultural_tier is 1 or 2 (or historical narrative mode): appends VIETNAMESE_CANONICAL_NEGATIVE_PROMPT
      to ban foreign distortion (Hanfu, Kimono, Hanbok, Samurai, Ninja).
    - If genre is 'school': appends MODERN_SCHOOL_EXCLUSIONS.
    """
    neg = BASE_NEGATIVE_PROMPT
    genre_l = (genre or "").lower()

    if cultural_tier in (1, 2) or (narrative_mode and str(narrative_mode).lower() in ("chinh_su", "da_su", "strict_historical", "historical_fiction")):
        neg = f"{neg}, {VIETNAMESE_CANONICAL_NEGATIVE_PROMPT}"

    if genre_l == "school":
        neg = f"{neg}, {MODERN_SCHOOL_EXCLUSIONS}"

    return neg

def get_cloudflare_token():
    return os.environ.get("CLOUDFLARE_API_TOKEN", "")

def get_account_id():
    return os.environ.get("CLOUDFLARE_ACCOUNT_ID", "c349c6c7357e310e5032506f7efe5d42")

def get_deterministic_comic_seed(story_id: int | None = 1) -> int:
    """
    Calculates a synchronized deterministic seed based on story ID.
    Locks diffusion latent noise across all manga panels in the story.
    Returns an integer in the range [100000, 999999].
    """
    anchor_id = int(story_id) if story_id is not None else 1
    return (int(anchor_id) * 7919 + 4289000) % 900000 + 100000

def generate_image_cf(
    prompt: str,
    seed: int | None = None,
    negative_prompt_suffix: Optional[str] = None,
    layout_type: str = "square",
    custom_negative_prompt: Optional[str] = None,
    cultural_tier: Optional[int] = None,
    narrative_mode: Optional[str] = None,
    genre: str = "school"
) -> bytes:
    """
    Calls Cloudflare Workers AI Text-to-Image model with fallback chain.
    Applies master negative prompt and deterministic seed.
    Returns binary image data (bytes).
    """
    token = get_cloudflare_token()
    account_id = get_account_id()

    if not token:
        raise Exception("CLOUDFLARE_API_TOKEN not configured")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    negative_prompt = get_master_negative_prompt(
        genre=genre,
        cultural_tier=cultural_tier,
        narrative_mode=narrative_mode
    )
    suffix = negative_prompt_suffix or custom_negative_prompt
    if suffix:
        negative_prompt = f"{negative_prompt}, {suffix.strip(' ,')}"

    payload = {
        "prompt": prompt,
        "negative_prompt": negative_prompt
    }
    if seed is not None:
        payload["seed"] = int(seed)
    
    last_error = None
    for model in CF_MODELS:
        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=25)
            if response.status_code == 200 and len(response.content) > 500:
                return response.content
            else:
                last_error = f"{model}: status={response.status_code}, body={response.text[:200]}"
                print(f"[CF AI] Model failed: {last_error}")
        except requests.exceptions.Timeout:
            last_error = f"{model}: timeout after 25s"
            print(f"[CF AI] Model timeout: {last_error}")
        except Exception as e:
            last_error = f"{model}: {e}"
            print(f"[CF AI] Model error: {last_error}")
    
    raise Exception(f"All Cloudflare models failed. Last error: {last_error}")


def format_pollinations_prompt(prompt: str, max_len: int = 500) -> str:
    """
    Prepares a clean, semantic-safe prompt for Pollinations fallback image generation.
    - Slices cleanly at comma/sentence boundaries instead of arbitrary character cuts.
    - Preserves setting anchor, action gesture, and character DNA without mid-word truncations.
    - Fits within safe URL length limits for HTTP GET requests.
    """
    if not prompt or not isinstance(prompt, str):
        return "black and white manga drawing, monochrome ink on white paper, Japanese manga style, screentone, no color"

    clean_p = prompt.strip()
    if len(clean_p) <= max_len:
        target = clean_p
    else:
        # Extract setting anchor if present to guarantee spatial preservation
        setting_match = re.search(r'\bsetting:\s*([^,]+(?:,[^,]+){0,2})', clean_p, re.IGNORECASE)
        setting_clause = setting_match.group(0).strip() if setting_match else ""

        # Slice cleanly at last comma or period within max_len
        cutoff = clean_p[:max_len]
        last_delim = max(cutoff.rfind(','), cutoff.rfind('.'))
        if last_delim > max_len // 2:
            target = cutoff[:last_delim].strip(' ,.-')
        else:
            last_space = cutoff.rfind(' ')
            target = cutoff[:last_space].strip(' ,.-') if last_space > 0 else cutoff

        # Guarantee setting anchor is preserved
        if setting_clause and setting_clause.lower() not in target.lower():
            target = f"{target}, {setting_clause}"

    # Clean double commas and trailing punctuation
    target = re.sub(r'[,.\s]*,[,.\s]*', ', ', target).strip(' ,.-')
    return f"black and white manga drawing, monochrome ink on white paper, Japanese manga style, {target}, screentone, no color"


def get_cached_or_generate_image(
    panel_id: int,
    prompt: str,
    seed: int | None = None,
    story_id: Optional[int] = None,
    negative_prompt_suffix: Optional[str] = None,
    custom_negative_prompt: Optional[str] = None,
    cultural_tier: Optional[int] = None,
    narrative_mode: Optional[str] = None,
    genre: str = "school"
) -> tuple[bytes, str]:
    """
    Fetches image from disk cache if available.
    Otherwise attempts Cloudflare Workers AI with deterministic seed synchronized by story_id,
    with fallback to Pollinations B&W manga, then writes to disk cache.
    Returns (image_bytes, media_type).
    """
    cache_path = os.path.join(CACHE_DIR, f"panel_{panel_id}.jpg")
    
    # 1. Check local persistent disk cache
    if os.path.isfile(cache_path) and os.path.getsize(cache_path) > 1000:
        try:
            with open(cache_path, "rb") as f:
                img_bytes = f.read()
            media_type = "image/jpeg" if img_bytes[:2] == b'\xff\xd8' else "image/png"
            return img_bytes, media_type
        except Exception as e:
            print(f"[Comic Cache] Failed to read cached panel_{panel_id}: {e}")

    # 2. Determine synchronized deterministic seed
    if seed is not None:
        panel_seed = int(seed)
    elif story_id is not None:
        panel_seed = get_deterministic_comic_seed(story_id)
    else:
        panel_seed = (4289000 + (panel_id % 1000))
    try:
        suffix = negative_prompt_suffix or custom_negative_prompt
        img_bytes = generate_image_cf(
            prompt,
            seed=panel_seed,
            negative_prompt_suffix=suffix,
            cultural_tier=cultural_tier,
            narrative_mode=narrative_mode,
            genre=genre
        )
    except Exception as e:
        print(f"[Comic Image] Cloudflare AI unavailable ({e}). Falling back to Pollinations...")
        try:
            bw_prompt = format_pollinations_prompt(prompt)
            safe_prompt = urllib.parse.quote(bw_prompt)
            fallback_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=800&height=800&nologo=true&seed={panel_seed}"
            resp = requests.get(fallback_url, timeout=20)
            if resp.status_code == 200 and len(resp.content) > 500:
                img_bytes = resp.content
        except Exception as p_err:
            print(f"[Comic Image] Pollinations fallback also failed ({p_err})")

    if not img_bytes:
        raise Exception(f"Could not render image for panel {panel_id}")

    # 2.5: Server-side Pillow monochrome enforcement — eliminates color leak from ANY source
    try:
        img_bytes = process_manga_monochrome(img_bytes)
    except Exception as mono_err:
        print(f"[Comic Image] Monochrome post-processing failed ({mono_err}), using raw bytes")

    # 3. Save to disk cache
    try:
        with open(cache_path, "wb") as f:
            f.write(img_bytes)
    except Exception as e:
        print(f"[Comic Cache] Failed to save panel_{panel_id}: {e}")

    media_type = "image/jpeg" if img_bytes[:2] == b'\xff\xd8' else "image/png"
    return img_bytes, media_type


def process_manga_monochrome(image_bytes: bytes) -> bytes:
    """
    Server-side Pillow post-processing to enforce 100% monochrome manga.
    Converts any image to grayscale with autocontrast for clean lineart appearance.
    Returns JPEG bytes. If PIL is not installed, gracefully returns raw image_bytes.
    """
    if not HAS_PIL:
        return image_bytes

    try:
        img = Image.open(io.BytesIO(image_bytes))
        # Convert to grayscale (removes all color information)
        gray = img.convert('L')
        # Apply autocontrast to enhance lineart contrast (like screentone manga)
        enhanced = ImageOps.autocontrast(gray, cutoff=1)
        # Export as high-quality JPEG
        output = io.BytesIO()
        enhanced.save(output, format="JPEG", quality=92)
        return output.getvalue()
    except Exception as e:
        print(f"[Comic Image] process_manga_monochrome error: {e}")
        return image_bytes


# Valid minimal 1x1 grayscale JPEG bytes for emergency fallback when PIL is absent
_FALLBACK_1X1_JPEG = (
    b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06'
    b'\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14'
    b'\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x0b'
    b'\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01'
    b'\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xda\x00\x08\x01'
    b'\x01\x00\x00?\x00\xbf\x00\xff\xd9'
)


def get_guaranteed_monochrome_fallback(panel_index: int = 0) -> bytes:
    """
    Generates a guaranteed-available monochrome placeholder JPEG
    for use when all image generation sources fail.
    Returns JPEG bytes that can be served directly with HTTP 200.
    """
    if not HAS_PIL:
        return _FALLBACK_1X1_JPEG

    try:
        img = Image.new('L', (800, 800), color=245)  # Light gray background

        draw = ImageDraw.Draw(img)
        # Draw manga-style panel border
        draw.rectangle([10, 10, 789, 789], outline=30, width=3)

        # Draw diagonal screentone-like pattern
        for y in range(20, 780, 40):
            for x in range(20, 780, 40):
                draw.ellipse([x, y, x + 3, y + 3], fill=200)

        # Draw center text
        text = f"Panel {panel_index + 1}"
        try:
            font = ImageFont.truetype("arial.ttf", 32)
        except (IOError, OSError):
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        draw.text(((800 - text_w) // 2, (800 - text_h) // 2), text, fill=100, font=font)

        output = io.BytesIO()
        img.save(output, format="JPEG", quality=90)
        return output.getvalue()
    except Exception as e:
        print(f"[Comic Image] get_guaranteed_monochrome_fallback error: {e}")
        return _FALLBACK_1X1_JPEG
