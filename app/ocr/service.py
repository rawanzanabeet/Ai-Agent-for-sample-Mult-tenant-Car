from app.ocr.utils import download_and_open_image, run_ocr
from app.ocr.parser import extract_fields
from app.ocr.validator import validate_license, assess_car_risk


def analyze_driving_license_service(
    image_url: str,
    country: str | None = None,
    car: dict | None = None,
):
    image = download_and_open_image(image_url)
    ocr_text = run_ocr(image)

    fields = extract_fields(ocr_text, country)
    validation = validate_license(fields)
    car_risk = assess_car_risk(
        car,
        validation["valid"] and not validation["requires_review"]
    )

    return {
        "source": "local_ocr",
        "ocr_text": ocr_text,
        "extracted": fields,
        "validation": validation,
        "car_risk": car_risk,
    }
