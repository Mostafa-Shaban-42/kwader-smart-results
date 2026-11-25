import pandas as pd
from backend.services.validation import validate_dataframe

def test_exceeds_variable_max():
    # Physiology max is 50, student got 60 -> error, must mention 50 in reason
    df = pd.DataFrame([
        {"student_id": "001254", "student_name": "A", "academic_year": "first_year", "physiology": 60},
    ])
    errs, _ = validate_dataframe(df, ["physiology"], {"physiology": 50.0}, True)
    assert errs[0]["code"] == "EXCEEDS_MAX"
    assert "50" in errs[0]["reason_ar"]

def test_valid_with_variable_max():
    # 40 / 50 is valid, should NOT error
    df = pd.DataFrame([
        {"student_id": "001254", "student_name": "A", "academic_year": "first_year", "physiology": 40},
    ])
    errs, _ = validate_dataframe(df, ["physiology"], {"physiology": 50.0}, True)
    assert len(errs) == 0

def test_small_max_marks_10_and_20():
    df = pd.DataFrame([
        {"student_id": "001254", "student_name": "A", "academic_year": "first_year", "quiz": 9, "practical": 20},
    ])
    errs, _ = validate_dataframe(df, ["quiz", "practical"], {"quiz": 10.0, "practical": 20.0}, True)
    assert len(errs) == 0

def test_no_max_row_warning():
    df = pd.DataFrame([
        {"student_id": "001254", "student_name": "A", "academic_year": "first_year", "math": 90},
    ])
    errs, warns = validate_dataframe(df, ["math"], {"math": 100.0}, False)
    assert any(w["code"] == "NO_MAX_ROW" for w in warns)

def test_duplicate_explains_reason():
    df = pd.DataFrame([
        {"student_id": "001254", "student_name": "A", "academic_year": "first_year", "math": 90},
        {"student_id": "001254", "student_name": "B", "academic_year": "first_year", "math": 80},
    ])
    errs, _ = validate_dataframe(df, ["math"], {"math": 100.0}, True)
    assert any(e["code"] == "DUPLICATE_ID" and "السبب" in e["reason_ar"] for e in errs)

def test_calculation_with_variable_max():
    # This is in statistics, but validate total logic: 85/100 + 40/50 + 18/20 = 143 / 170 = 84.11%
    from backend.services.statistics import calculate_result
    rec = {"subjects": {"anatomy": {"obtained": 85, "maximum": 100}, "physiology": {"obtained": 40, "maximum": 50}, "practical": {"obtained": 18, "maximum": 20}}}
    out = calculate_result(rec)
    assert out["total_obtained"] == 143
    assert out["total_maximum"] == 170
    assert abs(out["percentage"] - 84.1176) < 0.01