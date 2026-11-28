"""Pure calculations. No Firebase."""
from backend.core.config import GRADE_THRESHOLDS
def grade_from_percentage(pct: float) -> tuple[str, str]:
    for th, en, ar in GRADE_THRESHOLDS:
        if pct >= th: return en, ar
    return "Fail", "راسب"

def calculate_result(record: dict) -> dict:
    subjects = record["subjects"]
    total_obtained = sum(v["obtained"] for v in subjects.values())
    total_max = sum(v["maximum"] for v in subjects.values())
    pct = round((total_obtained / total_max * 100) if total_max > 0 else 0.0, 2)
    en, ar = grade_from_percentage(pct)
    record.update({"total_obtained": total_obtained, "total_maximum": total_max, "percentage": pct, "grade": en, "grade_ar": ar})
    return record

def year_statistics(results: list[dict]) -> dict:
    if not results: return {"count": 0, "average": 0, "median": 0, "highest": 0, "lowest": 0, "std_dev": 0, "pass_rate": 0, "fail_rate": 0}
    import statistics
    pcts = [r["percentage"] for r in results]
    passed = sum(1 for p in pcts if p >= 60)
    return {"count": len(results), "average": round(sum(pcts)/len(pcts), 2), "median": round(statistics.median(pcts), 2), "highest": max(pcts), "lowest": min(pcts), "std_dev": round(statistics.pstdev(pcts), 2) if len(pcts)>1 else 0, "pass_rate": round(passed/len(pcts)*100, 2), "fail_rate": round((len(pcts)-passed)/len(pcts)*100, 2)}

def grade_distribution(results: list[dict]) -> dict:
    dist = {"Excellent": 0, "Very Good": 0, "Good": 0, "Pass": 0, "Fail": 0}
    for r in results: dist[r["grade"]] = dist.get(r["grade"], 0) + 1
    return dist

def motivation_for_student(rank: int, total: int, pct: float) -> dict:
    """Dynamic message + badge based on rank/percentage. Always respectful."""
    if rank == 1:
        return {"badge": "crown", "icon": "👑", "title": "Outstanding! You Are Ranked 1st", "message": "Congratulations! You are ranked 1st out of {} students. You are a true inspiration for Kawader. Keep shining!".format(total), "color": "gold"}
    if rank <= 3:
        return {"badge": "crown", "icon": "👑", "title": f"Amazing! You Are Ranked {rank}rd" if rank==3 else f"Amazing! You Are Ranked {rank}th", "message": f"Congratulations! You are ranked {rank} out of {total} students. You are among the top students. We are so proud of you.", "color": "gold"}
    if rank <= max(3, total*0.1):
        return {"badge": "star", "icon": "⭐", "title": "Excellent Work!", "message": f"Excellent work! You are ranked {rank} out of {total} students, among the top 10%. We are so proud of you.", "color": "gold"}
    if pct >= 70:
        return {"badge": "good", "icon": "💜", "title": "Great Job!", "message": f"Great job! You are ranked {rank} out of {total} students. A little more effort and you will be among the top. We believe in you.", "color": "purple"}
    if pct >= 60:
        return {"badge": "encourage", "icon": "💪", "title": "You Can Do It!", "message": f"You are ranked {rank} out of {total} students. We believe in you. Keep going, your next result will be better.", "color": "purple"}
    return {"badge": "support", "icon": "💛", "title": "We Believe In You", "message": "Dear student, please do not give up. This is just a step, not the end. Please contact your academic advisor, we will help you succeed.", "color": "support"}