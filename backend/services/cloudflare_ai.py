import os
import requests

CLOUDFLARE_API_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", "")
ACCOUNT_ID = "c349c6c7357e310e5032506f7efe5d42"

def generate_image_cf(prompt: str):
    """
    Calls Cloudflare Workers AI Text-to-Image model.
    Returns binary image data (bytes).
    """
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/@cf/stabilityai/stable-diffusion-xl-base-1.0"
    
    headers = {
        "Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": prompt
    }
    
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Cloudflare API Error: {response.status_code} - {response.text}")
