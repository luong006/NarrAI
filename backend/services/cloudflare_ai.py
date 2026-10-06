import os
import re
import requests
import urllib.parse
import io

from typing import Optional, Tuple

try:
    from PIL import Image, ImageOps
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    Image = None
    ImageOps = None

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
    genre: str = "",
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
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "")
    if not account_id:
        raise Exception(
            "CLOUDFLARE_ACCOUNT_ID environment variable is not configured. "
            "Please set it in your Render dashboard or backend/.env file."
        )
    return account_id

def get_deterministic_comic_seed(story_id: int | None = 1) -> int:
    """
    Calculates a stable base seed for a story; each panel derives its own seed from it.
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
    genre: str = ""
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
            if response.status_code == 200 and _is_valid_image_payload(response.content):
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
        # Keep character/action details early, but reserve room for the environment anchor.
        setting_match = re.search(r'\bsetting:\s*[^,]+(?:,[^,]+){0,2}', clean_p, re.IGNORECASE)
        setting_clause = setting_match.group(0).strip() if setting_match else ""
        prompt_without_setting = clean_p
        if setting_match:
            prompt_without_setting = f"{clean_p[:setting_match.start()]}, {clean_p[setting_match.end():]}"
        prompt_budget = max(120, max_len - len(setting_clause) - 2)
        cutoff = prompt_without_setting[:prompt_budget]
        last_delim = max(cutoff.rfind(','), cutoff.rfind('.'))
        if last_delim > prompt_budget // 2:
            target = cutoff[:last_delim].strip(' ,.-')
        else:
            last_space = cutoff.rfind(' ')
            target = cutoff[:last_space].strip(' ,.-') if last_space > 0 else cutoff

        if setting_clause:
            target = f"{target}, {setting_clause}"

    # Clean double commas and trailing punctuation
    target = re.sub(r'[,.\s]*,[,.\s]*', ', ', target).strip(' ,.-')
    return f"black and white manga drawing, monochrome ink on white paper, Japanese manga style, {target}, screentone, no color"


def _is_valid_image_payload(image_bytes: Optional[bytes]) -> bool:
    if not image_bytes or len(image_bytes) <= 500:
        return False
    if HAS_PIL:
        try:
            image = Image.open(io.BytesIO(image_bytes))
            image.verify()
            return True
        except Exception:
            return False
    return image_bytes.startswith((b"\xff\xd8", b"\x89PNG\r\n\x1a\n", b"GIF87a", b"GIF89a", b"RIFF"))


def get_cached_or_generate_image(
    panel_id: int,
    prompt: str,
    seed: int | None = None,
    story_id: Optional[int] = None,
    negative_prompt_suffix: Optional[str] = None,
    custom_negative_prompt: Optional[str] = None,
    cultural_tier: Optional[int] = None,
    narrative_mode: Optional[str] = None,
    genre: str = "",
    force_refresh: bool = False,
) -> tuple[bytes, str]:
    """
    Fetches image from disk cache if available.
    Otherwise attempts Cloudflare Workers AI with a deterministic panel-specific seed,
    with fallback to Pollinations B&W manga, then writes to disk cache.
    Returns (image_bytes, media_type).
    """
    cache_path = os.path.join(CACHE_DIR, f"panel_{panel_id}.jpg")
    
    # A retry must not serve the image that just failed at the client, even if
    # it happens to be a valid image payload in the local cache.
    if force_refresh:
        try:
            os.remove(cache_path)
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"[Comic Cache] Could not clear cached panel_{panel_id} before retry: {e}")

    # 1. Check local persistent disk cache unless the user explicitly retried.
    if not force_refresh and os.path.isfile(cache_path) and os.path.getsize(cache_path) > 1000:
        try:
            with open(cache_path, "rb") as f:
                img_bytes = f.read()
            if _is_valid_image_payload(img_bytes):
                media_type = "image/jpeg" if img_bytes[:2] == b'\xff\xd8' else "image/png"
                return img_bytes, media_type
            print(f"[Comic Cache] Cached panel_{panel_id} is not a valid image; regenerating")
            os.remove(cache_path)
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"[Comic Cache] Failed to read cached panel_{panel_id}: {e}")

    # Keep a stable story-level seed while giving each panel a distinct composition.
    if seed is not None:
        story_seed = int(seed)
    elif story_id is not None:
        story_seed = get_deterministic_comic_seed(story_id)
    else:
        story_seed = get_deterministic_comic_seed(panel_id)
    panel_seed = 100000 + ((story_seed - 100000 + panel_id * 7919) % 900000)
    img_bytes = None
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
            if resp.status_code == 200 and _is_valid_image_payload(resp.content):
                img_bytes = resp.content
        except Exception as p_err:
            print(f"[Comic Image] Pollinations fallback also failed ({p_err})")

    if not img_bytes or not _is_valid_image_payload(img_bytes):
        raise RuntimeError(f"Could not render image for panel {panel_id}: all image providers failed")

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
