from services.comfyui_service import generate_image_comfyui, is_comfyui_available


def generate_comic_panel_image(prompt: str, seed: int = 42) -> bytes:
    """Generate comic panel image using ComfyUI GPU backend."""
    return generate_image_comfyui(prompt=prompt, seed=seed)
