"""Academic calculations only. All functions pure + unit-testable."""
from backend.core.config import GRADE_THRESHOLDS

def grade_from_percentage(pct: float) -> tuple[str, str]:
    """Return (grade_en, grade_ar) using school-approved thresholds."""
    for threshold, en, ar in GRADE_THRESHOLDS:
        if pct >= threshold:
            return en, ar
    return "Fail", "راسب"

def calculate_result(record: dict) -> dict:
    """Calculate total, percentage, grade. Handles total_maximum == 0."""
    subjects = record["subjects"]
    total_obtained = sum(v["obtained"] for v in subjects.values())
    total_max = sum(v["maximum"] for v in subjects.values())
    pct = round((total_obtained / total_max * 100) if total_max > 0 else 0.0, 4)
    grade_en, grade_ar = grade_from_percentage(pct)
    record["total_obtained"] = total_obtained
    record["total_maximum"] = total_max
    record["percentage"] = pct
    record["grade"] = grade_en
    record["grade_ar"] = grade_ar
    return record

def year_statistics(results: list[dict]) -> dict:
    if not results:
        return {"count": 0, "average": 0, "median": 0, "highest": 0, "lowest": 0, "std_dev": 0, "pass_rate": 0, "fail_rate": 0}
    import statistics
    pcts = [r["percentage"] for r in results]
    passed = sum(1 for p in pcts if p >= 60)
    return {
        "count": len(results),
        "average": round(sum(pcts) / len(pcts), 2),
        "median": round(statistics.median(pcts), 2),
        "highest": max(pcts),
        "lowest": min(pcts),
        "std_dev": round(statistics.pstdev(pcts), 2) if len(pcts) > 1 else 0,
        "pass_rate": round(passed / len(pcts) * 100, 2),
        "fail_rate": round((len(pcts) - passed) / len(pcts) * 100, 2),
    }

def grade_distribution(results: list[dict]) -> dict:
    dist = {"Excellent": 0, "Very Good": 0, "Good": 0, "Pass": 0, "Fail": 0}
    for r in results:
        dist[r["grade"]] = dist.get(r["grade"], 0) + 1
    return dist