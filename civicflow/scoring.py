"""Transparent, illustrative priority heuristic (max 100). Not an official risk score."""

CATEGORIES = [
    "Road Damage",
    "Waste & Sanitation",
    "Water & Drainage",
    "Streetlight & Electrical",
    "Public Safety",
    "Other",
]

CATEGORY_IMPACT = {
    "Road Damage": 12,
    "Waste & Sanitation": 7,
    "Water & Drainage": 10,
    "Streetlight & Electrical": 9,
    "Public Safety": 12,
    "Other": 4,
}

DEPARTMENTS = {
    "Road Damage": "Roads & Pavements",
    "Waste & Sanitation": "Solid Waste & Sanitation",
    "Water & Drainage": "Water Supply & Drainage",
    "Streetlight & Electrical": "Street Lighting & Electrical",
    "Public Safety": "Public Safety & Disaster Response",
    "Other": "General Civic Services",
}

BASE = 10
SAFETY_POINTS = 25
DURATION_POINTS = 8
RELATED_EACH = 5
RELATED_CAP = 15
HIGH_AT = 65
MEDIUM_AT = 38


def build_reasons(category, severity, safety_evidence, duration_evidence, related_count):
    reasons = [
        {"factor": "base", "points": BASE, "detail": "Every report starts with a base score."},
        {"factor": "category", "points": CATEGORY_IMPACT[category], "detail": f"{category} reports carry this weight."},
        {"factor": "severity", "points": severity * 5, "detail": f"Assessed {severity} of 5, 5 points per level."},
    ]
    if safety_evidence:
        reasons.append({"factor": "safety", "points": SAFETY_POINTS, "detail": f"The report mentions: {safety_evidence}."})
    if duration_evidence:
        reasons.append({"factor": "duration", "points": DURATION_POINTS, "detail": f"The report mentions: {duration_evidence}."})
    return set_related(reasons, related_count)


def set_related(reasons, related_count):
    """Replace/add/remove the related-reports factor (used again when a cluster grows)."""
    reasons = [r for r in reasons if r["factor"] != "related"]
    pts = min(RELATED_CAP, RELATED_EACH * max(0, related_count))
    if pts:
        noun = "report" if related_count == 1 else "reports"
        reasons.append({
            "factor": "related",
            "points": pts,
            "detail": f"{related_count} possibly related {noun} nearby, 5 points each, capped at 15.",
        })
    return reasons


def total(reasons) -> int:
    return max(0, min(100, sum(r["points"] for r in reasons)))


def label(score: int) -> str:
    if score >= HIGH_AT:
        return "High"
    if score >= MEDIUM_AT:
        return "Medium"
    return "Low"
