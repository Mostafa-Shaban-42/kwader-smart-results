"""Excel reading using Smart Parser. No validation, no calculation here."""
import io
import pandas as pd
from backend.services.smart_parser import parse_dataframe

def read_excel(file_bytes: bytes, forced_year: str | None = None) -> tuple[pd.DataFrame, dict[str, float], bool, list[str]]:
    df_raw = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl", header=None)
    df, max_map, has_max, subjects = parse_dataframe(df_raw, forced_year=forced_year)
    return df, max_map, has_max, subjects

def detect_subjects(df: pd.DataFrame) -> list[str]:
    reserved = {"student_id", "student_name", "academic_year"}
    return [c for c in df.columns if c not in reserved]

def df_to_records(df: pd.DataFrame, subjects: list[str], subject_max_map: dict[str, float]) -> list[dict]:
    records = []
    for _, row in df.iterrows():
        if row.isna().all(): continue
        subj = {}
        for s in subjects:
            try: obtained = float(row[s])
            except: obtained = 0.0
            subj[s] = {"obtained": obtained, "maximum": subject_max_map.get(s, 100.0)}
        records.append({"student_id": str(row["student_id"]), "student_name": str(row["student_name"]), "academic_year": str(row["academic_year"]), "subjects": subj, "active": True})
    return records