import re
from dateutil import parser as date_parser


def parse_date(raw: str):
    try:
        dt = date_parser.parse(raw, dayfirst=True)

        two_digit_year = bool(
            re.search(r"\b\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2}\b", raw)
        )

        if two_digit_year and dt.year > 2025:
            dt = dt.replace(year=dt.year - 100)

        return dt.date().isoformat()
    except Exception:
        return None


def extract_fields(text: str, country: str | None = None) -> dict:
    fields = {
        "license_number": None,
        "expiry_date": None,
        "issue_date": None,
        "birth_date": None,
        "detected_country": None,
        "country_hint_used": False,
    }

    upper = text.upper()

    # ---------- COUNTRY DETECTION ----------
    if "USA" in upper or "PENNSYLVANIA" in upper or " PA " in upper:
        fields["detected_country"] = "US"
    elif "DVLA" in upper or "DRIVING LICENCE" in upper:
        fields["detected_country"] = "UK"

    # ---------- UK LICENSE NUMBER ----------
    clean = re.sub(r"[^A-Z0-9]", "", upper)
    uk_dl = re.search(r"[A-Z]{5}\d{6}[A-Z]{2}[A-Z0-9]{3}", clean)
    if uk_dl:
        fields["license_number"] = uk_dl.group(0)

    # ---------- DATE BY FIELD NUMBER (US-FIRST) ----------
    def find_date_by_field_number(field_numbers):
        for n in field_numbers:
            m = re.search(
                rf"{n}\s*[A-Z]*\s*[:\-]?\s*(\d{{1,2}}[\/\-\.]\d{{1,2}}[\/\-\.]\d{{2,4}})",
                upper,
            )
            if m:
                return parse_date(m.group(1))
        return None

    # US official numbering
    fields["birth_date"] = find_date_by_field_number(["3"])
    fields["issue_date"] = find_date_by_field_number(["4A"])
    fields["expiry_date"] = find_date_by_field_number(["4B"])

    # ---------- FALLBACK (KEYWORDS) ----------
    if not fields["birth_date"]:
        fields["birth_date"] = _find_by_keywords(upper, ["DOB", "BIRTH"])
    if not fields["issue_date"]:
        fields["issue_date"] = _find_by_keywords(upper, ["ISS", "ISSUE"])
    if not fields["expiry_date"]:
        fields["expiry_date"] = _find_by_keywords(upper, ["EXP", "EXPIRE"])

    if country:
        fields["country_hint_used"] = country.lower() in upper.lower()

    return fields


def _find_by_keywords(text: str, keywords: list[str]):
    for k in keywords:
        m = re.search(
            k + r".{0,10}(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})",
            text,
        )
        if m:
            return parse_date(m.group(1))
    return None
