"""Competition Ranking 1,2,2,4. Grouped by academic_year. Also adds batch stats."""
from collections import defaultdict
def assign_ranking(results: list[dict]) -> list[dict]:
    by_year: dict[str, list[dict]] = defaultdict(list)
    for r in results: by_year[r["academic_year"]].append(r)
    ranked = []
    for year, group in by_year.items():
        sorted_group = sorted(group, key=lambda x: x["total_obtained"], reverse=True)
        rank, prev = 0, None
        for i, r in enumerate(sorted_group):
            if r["total_obtained"] != prev:
                rank = i + 1; prev = r["total_obtained"]
            r["rank"] = rank; r["total_students"] = len(group)
            ranked.append(r)
    return ranked