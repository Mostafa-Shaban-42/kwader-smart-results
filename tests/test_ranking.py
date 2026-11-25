from backend.services.ranking import assign_ranking
from backend.services.statistics import calculate_result

def test_competition_ranking():
    data = [
        {"academic_year":"first_year","total_obtained":450},
        {"academic_year":"first_year","total_obtained":430},
        {"academic_year":"first_year","total_obtained":430},
        {"academic_year":"first_year","total_obtained":410},
    ]
    out = assign_ranking(data)
    assert sorted([r["rank"] for r in out]) == [1,2,2,4]

def test_ranking_never_mixes_years():
    data = [
        {"academic_year":"first_year","total_obtained":400},
        {"academic_year":"second_year","total_obtained":400},
    ]
    out = assign_ranking(data)
    assert all(r["rank"]==1 for r in out)

def test_calculation_example_from_rules():
    rec = {"subjects": {"math":{"obtained":85,"maximum":100},"physics":{"obtained":90,"maximum":100},"chemistry":{"obtained":75,"maximum":100}}}
    out = calculate_result(rec)
    assert out["total_obtained"] == 250
    assert out["total_maximum"] == 300
    assert abs(out["percentage"] - 83.3333) < 0.001
    assert out["grade"] == "Very Good"

def test_total_max_zero_no_crash():
    rec = {"subjects": {}}
    out = calculate_result(rec)
    assert out["percentage"] == 0