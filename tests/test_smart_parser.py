# tests/test_smart_parser.py
import pandas as pd
from backend.services.smart_parser import parse_dataframe
def test_arabic_columns():
    df = pd.DataFrame([["رقم الطالب","اسم الطالب","التمريض"],["001254","Ahmed",85]])
    out, max_map, has_max, subjects = parse_dataframe(df)
    assert "student_id" in out.columns and "student_name" in out.columns
    assert out.iloc[0]["student_id"] == "001254"
def test_max_anywhere():
    df = pd.DataFrame([["id","name","math"],["MAX","",100],["001","A",90]])
    out, max_map, has_max, _ = parse_dataframe(df)
    assert has_max and max_map["math"] == 100.0 and len(out)==1