import sys
import json
import urllib.request
import urllib.error

def get_ngrok_public_url():
    """Queries ngrok local API at port 4040 to find the active HTTPS public tunnel URL."""
    try:
        req = urllib.request.Request("http://127.0.0.1:4040/api/tunnels")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for t in data.get("tunnels", []):
                pub = t.get("public_url", "")
                if pub.startswith("https://"):
                    return pub
                elif pub.startswith("http://"):
                    return pub
    except Exception as e:
        print(f"[!] Khong the lay duong link ngrok tu 127.0.0.1:4040: {e}")
        print("    Hay chac chan ban da chay lenh: ngrok http 8188")
    return None

def update_render_backend(render_url: str, ngrok_url: str):
    clean_url = render_url.rstrip("/")
    api_endpoint = f"{clean_url}/api/comic/comfyui/set-url"
    print(f"[*] Dang cap nhat ComfyUI URL toi Backend Render: {api_endpoint}")
    print(f"    Target URL: {ngrok_url}")
    
    payload = json.dumps({"url": ngrok_url}).encode("utf-8")
    req = urllib.request.Request(
        api_endpoint,
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": "NarrAI-Ngrok-Sync/1.0"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            print("[✓] THANH CONG! Backend Render da nhan dien ComfyUI cua ban:")
            print(json.dumps(res_data, indent=2, ensure_ascii=False))
    except urllib.error.HTTPError as e:
        print(f"[x] Loi HTTP tu Render ({e.code}): {e.read().decode('utf-8', errors='ignore')}")
    except Exception as e:
        print(f"[x] Khong the ket noi toi Render ({render_url}): {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Su dung: python sync_ngrok_to_render.py <RENDER_BACKEND_URL>")
        print("Vi du:   python sync_ngrok_to_render.py https://narrai-backend.onrender.com")
        sys.exit(1)
        
    render_backend = sys.argv[1].strip()
    ngrok_url = get_ngrok_public_url()
    if ngrok_url:
        print(f"[OK] Da tim thay ngrok URL dang chay: {ngrok_url}")
        update_render_backend(render_backend, ngrok_url)
    else:
        print("[!] Hay bat ngrok truoc: chay file start_ngrok_comfyui.bat hoac go 'ngrok http 8188'")
