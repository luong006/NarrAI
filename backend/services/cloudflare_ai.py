import os
import requests
import urllib.parse

# Local persistent disk cache for rendered panels
CACHE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static", "comic_cache"))
os.makedirs(CACHE_DIR, exist_ok=True)

# Model fallback chain: fastest first, then higher quality
CF_MODELS = [
    "@cf/bytedance/stable-diffusion-xl-lightning",
    "@cf/lykon/dreamshaper-8-lcm",
    "@cf/stabilityai/stable-diffusion-xl-base-1.0",
]

def get_cloudflare_token():
    return os.environ.get("CLOUDFLARE_API_TOKEN", "")

def get_account_id():
    return os.environ.get("CLOUDFLARE_ACCOUNT_ID", "c349c6c7357e310e5032506f7efe5d42")

def generate_image_cf(prompt: str) -> bytes:
    """
    Calls Cloudflare Workers AI Text-to-Image model with fallback chain.
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
    
    payload = {
        "prompt": prompt,
        "negative_prompt": "color, colorful, vibrant, saturated, photorealistic, photograph, photo, realistic, 3d render, digital painting, oil painting, watercolor, bright colors, rainbow, neon, warm tones, cool tones, skin color, blue sky, green grass, red, blue, yellow, orange, purple, pink, colored, CGI, real person, real face, real photo, camera"
    }
    
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


def get_cached_or_generate_image(panel_id: int, prompt: str) -> tuple[bytes, str]:
    """
    Fetches image from disk cache if available.
    Otherwise attempts Cloudflare Workers AI with fallback to Pollinations B&W manga,
    then writes to disk cache for instantaneous future loads.
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

    # 2. Generate via Cloudflare Workers AI
    img_bytes = None
    try:
        img_bytes = generate_image_cf(prompt)
    except Exception as e:
        print(f"[Comic Image] Cloudflare AI unavailable ({e}). Falling back to Pollinations...")
        try:
            bw_prompt = f"black and white manga drawing, monochrome ink on white paper, Japanese manga style, {prompt[:300]}, screentone, no color"
            safe_prompt = urllib.parse.quote(bw_prompt)
            fallback_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=800&height=800&nologo=true&seed={panel_id}"
            resp = requests.get(fallback_url, timeout=20)
            if resp.status_code == 200 and len(resp.content) > 500:
                img_bytes = resp.content
        except Exception as p_err:
            print(f"[Comic Image] Pollinations fallback also failed ({p_err})")

    if not img_bytes:
        raise Exception(f"Could not render image for panel {panel_id}")

    # 3. Save to disk cache
    try:
        with open(cache_path, "wb") as f:
            f.write(img_bytes)
    except Exception as e:
        print(f"[Comic Cache] Failed to save panel_{panel_id}: {e}")

    media_type = "image/jpeg" if img_bytes[:2] == b'\xff\xd8' else "image/png"
    return img_bytes, media_type
