"""Ranking only. Competition Ranking: 1,2,2,4. Grouped by academic_year."""
from collections import defaultdict

def assign_ranking(results: list[dict]) -> list[dict]:
    by_year: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        by_year[r["academic_year"]].append(r)
    ranked: list[dict] = []
    for year, group in by_year.items():
        sorted_group = sorted(group, key=lambda x: x["total_obtained"], reverse=True)
        rank = 0
        prev_score = None
        for i, r in enumerate(sorted_group):
            if r["total_obtained"] != prev_score:
                rank = i + 1
                prev_score = r["total_obtained"]
            r["rank"] = rank
            r["student_rank"] = rank
            ranked.append(r)
    return ranked