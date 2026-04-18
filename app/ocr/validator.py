from datetime import date

def validate_license(fields: dict) -> dict:
    blockers = []
    review = []
    warnings = []
    today = date.today()

    expiry = fields.get("expiry_date")

    if expiry:
        if date.fromisoformat(expiry) < today:
            blockers.append("LICENSE_EXPIRED")
    else:
        review.append("EXPIRY_DATE_MISSING")

    # License number is OPTIONAL for US
    if not fields.get("license_number"):
        if fields.get("detected_country") == "UK":
            review.append("LICENSE_NUMBER_MISSING")
        else:
            warnings.append("LICENSE_NUMBER_NOT_DETECTED")

    if fields.get("issue_date") and fields.get("birth_date"):
        if fields["issue_date"] <= fields["birth_date"]:
            blockers.append("ISSUE_BEFORE_BIRTH")

    return {
        "valid": len(blockers) == 0,
        "blockers": blockers,
        "review": review,
        "warnings": warnings,
        "requires_review": bool(review),
    }

def assess_car_risk(car: dict, license_valid: bool) -> dict:
    if not car:
        return None

    if not license_valid:
        return {
            "risk_level": "HIGH",
            "reasons": ["INVALID_LICENSE"],
        }

    risk = "LOW"
    reasons = []

    if car.get("engine_power", 0) > 200:
        risk = "MEDIUM"
        reasons.append("HIGH_ENGINE_POWER")

    if car.get("is_electric"):
        reasons.append("EV_REQUIRES_EXPERIENCE")

    if car.get("category") in {"SUV", "SPORT"}:
        risk = "MEDIUM"

    return {
        "risk_level": risk,
        "reasons": reasons,
    }
