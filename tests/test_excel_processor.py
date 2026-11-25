import io
import pandas as pd
from backend.services.excel_processor import read_excel, detect_subjects, df_to_records

def _make_excel_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return buf.getvalue()

def test_variable_max_marks():
    # Row 1 headers, Row 2 MAX, Row 3+ data
    df = pd.DataFrame([
        {"student_id": "MAX", "student_name": "", "academic_year": "", "anatomy": 100, "physiology": 50, "practical": 20},
        {"student_id": "001254", "student_name": "Ahmed", "academic_year": "first_year", "anatomy": 85, "physiology": 40, "practical": 18},
    ])
    data, max_map = read_excel(_make_excel_bytes(df))
    assert max_map == {"anatomy": 100.0, "physiology": 50.0, "practical": 20.0}
    assert len(data) == 1  # MAX row removed
    assert data.iloc[0]["student_id"] == "001254"
    records = df_to_records(data, ["anatomy", "physiology", "practical"], max_map)
    assert records[0]["subjects"]["anatomy"] == {"obtained": 85.0, "maximum": 100.0}
    assert records[0]["subjects"]["physiology"] == {"obtained": 40.0, "maximum": 50.0}
    assert records[0]["subjects"]["practical"] == {"obtained": 18.0, "maximum": 20.0}

def test_no_max_row_defaults_to_100():
    df = pd.DataFrame([
        {"student_id": "001254", "student_name": "Ahmed", "academic_year": "first_year", "anatomy": 85},
    ])
    data, max_map = read_excel(_make_excel_bytes(df))
    assert max_map == {"anatomy": 100.0}

def test_detect_subjects_dynamic():
    df = pd.DataFrame(columns=["student_id", "student_name", "academic_year", "a", "b", "c", "d", "e", "f", "g"])
    assert len(detect_subjects(df)) == 7

def test_empty_row_skipped():
    df = pd.DataFrame([
        {"student_id": "001254", "student_name": "A", "academic_year": "first_year", "math": 90},
        {"student_id": None, "student_name": None, "academic_year": None, "math": None},
    ])
    recs = df_to_records(df, ["math"], {"math": 100.0})
    assert len(recs) == 1