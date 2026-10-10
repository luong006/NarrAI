import urllib.parse

def generate_comic_panel_image(prompt: str, seed: int = 42):
    """Generate comic panel image using Pollinations AI (free, no API key needed)"""
    safe_prompt = urllib.parse.quote(prompt.strip() or "comic manga scene")
    return f"https://image.pollinations.ai/prompt/{safe_prompt}?width=800&height=800&nologo=true&seed={seed}"
