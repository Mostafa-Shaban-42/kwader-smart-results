"""Excel reading only. No validation, no calculation, no Firebase here.

Excel Format (V2 - Variable Max Marks):
Row 1: Headers -> student_id | student_name | academic_year | Anatomy | Physiology | ...
Row 2: MAX Row -> MAX | (empty) | (empty) | 100 | 50 | 20
Row 3+: Student data

If MAX row is missing, fallback is 100 for all subjects + warning in validation.
Never modifies original file. Reads into memory only. Single read.
"""
import io
import pandas as pd
from backend.services.validation import normalize_columns

RESERVED_COLUMNS = {"student_id", "student_name", "academic_year"}

def is_max_row(row: pd.Series) -> bool:
    """Check if this row is the MAX row: first cell == 'MAX' (case-insensitive)."""
    if row.empty:
        return False
    first = str(row.iloc[0]).strip().lower() if not pd.isna(row.iloc[0]) else ""
    return first == "max"

def read_excel(file_bytes: bytes) -> tuple[pd.DataFrame, dict[str, float], bool]:
    """
    Read Excel and extract max marks per subject.
    Returns: (df_without_max_row, subject_max_map, has_max_row)
    Example: subject_max_map = {"anatomy": 100.0, "physiology": 50.0, "practical": 20.0}
    """
    df = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl")
    df = normalize_columns(df)
    subjects = detect_subjects(df)
    subject_max_map: dict[str, float] = {}
    has_max_row = False

    if not df.empty and is_max_row(df.iloc[0]):
        has_max_row = True
        max_row = df.iloc[0]
        for subj in subjects:
            try:
                val = float(max_row[subj])
                if val <= 0:
                    val = 100.0
            except (ValueError, TypeError):
                val = 100.0
            subject_max_map[subj] = val
        df = df.iloc[1:].reset_index(drop=True)
    else:
        for subj in subjects:
            subject_max_map[subj] = 100.0

    if "student_id" in df.columns:
        df["student_id"] = df["student_id"].astype(str).str.strip()
        df["student_id"] = df["student_id"].str.replace(r"\.0$", "", regex=True)
        if len(df) > 0 and df["student_id"].str.isdigit().all():
            df["student_id"] = df["student_id"].str.zfill(6)

    if "student_name" in df.columns:
        df["student_name"] = df["student_name"].astype(str).str.strip()
        df["student_name"] = df["student_name"].str.replace(r"\s+", " ", regex=True)

    return df, subject_max_map, has_max_row

def detect_subjects(df: pd.DataFrame) -> list[str]:
    """Any column except the 3 reserved ones is a subject. Dynamic: 5, 7, 10 subjects."""
    return [c for c in df.columns if c not in RESERVED_COLUMNS]

def df_to_records(df: pd.DataFrame, subjects: list[str], subject_max_map: dict[str, float]) -> list[dict]:
    """
    Convert DataFrame to student records using per-subject max marks.
    Example: Anatomy obtained 85 / maximum 100, Physiology 40 / 50
    """
    records: list[dict] = []
    for _, row in df.iterrows():
        if row.isna().all():
            continue
        subjects_dict = {}
        for s in subjects:
            max_mark = subject_max_map.get(s, 100.0)
            try:
                obtained = float(row[s])
            except (ValueError, TypeError):
                obtained = 0.0
            subjects_dict[s] = {"obtained": obtained, "maximum": max_mark}
        records.append({
            "student_id": str(row["student_id"]),
            "student_name": str(row["student_name"]),
            "academic_year": str(row["academic_year"]),
            "subjects": subjects_dict,
            "active": True,
        })
    return records