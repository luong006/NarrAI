import os
import requests

CLOUDFLARE_API_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", "")
ACCOUNT_ID = "c349c6c7357e310e5032506f7efe5d42"

# Model fallback chain: fastest first, then higher quality
CF_MODELS = [
    "@cf/bytedance/stable-diffusion-xl-lightning",
    "@cf/lykon/dreamshaper-8-lcm",
    "@cf/stabilityai/stable-diffusion-xl-base-1.0",
]

def generate_image_cf(prompt: str):
    """
    Calls Cloudflare Workers AI Text-to-Image model with fallback chain.
    Returns binary image data (bytes).
    """
    if not CLOUDFLARE_API_TOKEN:
        raise Exception("CLOUDFLARE_API_TOKEN not configured")
    
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": prompt
    }
    
    last_error = None
    for model in CF_MODELS:
        url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/{model}"
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=25)
            if response.status_code == 200 and len(response.content) > 500:
                return response.content
            else:
                last_error = f"{model}: status={response.status_code}, body={response.text[:200]}"
                print(f"CF model failed: {last_error}")
        except requests.exceptions.Timeout:
            last_error = f"{model}: timeout after 25s"
            print(f"CF model timeout: {last_error}")
        except Exception as e:
            last_error = f"{model}: {e}"
            print(f"CF model error: {last_error}")
    
    raise Exception(f"All Cloudflare models failed. Last error: {last_error}")

