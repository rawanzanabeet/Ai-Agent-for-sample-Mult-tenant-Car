import requests
from PIL import Image
from io import BytesIO
import pytesseract


def download_and_open_image(url: str) -> Image.Image:
    try:
        res = requests.get(url, timeout=15)
        res.raise_for_status()
        return Image.open(BytesIO(res.content)).convert("RGB")
    except Exception as e:
        raise RuntimeError(f"Image download/open failed: {e}")


def run_ocr(image: Image.Image) -> str:
    try:
        return pytesseract.image_to_string(image, lang="eng")
    except Exception:
        raise RuntimeError("OCR engine not available")
