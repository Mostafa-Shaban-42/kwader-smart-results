"""
SMART PARSER - The brain of the system.
Accepts ANY Excel shape: any column names, any order, Arabic or English, MAX row anywhere.
Never rejects a file for column naming. It understands the file, not the other way around.
"""
import re
import pandas as pd

# Aliases for student_id
ID_ALIASES = ["student_id", "studentid", "id", "code", "seat", "seat_number", "seatnumber", "roll", "roll_number",
              "رقم_الطالب", "رقم_الجلوس", "كود_الطالب", "الكود", "الرقم", "رقم", "المسلسل"]
# Aliases for student_name
NAME_ALIASES = ["student_name", "studentname", "name", "full_name", "fullname", "student",
                "اسم_الطالب", "الاسم", "اسم", "الطالب", "الاسم_الكامل"]
# Aliases for academic_year
YEAR_ALIASES = ["academic_year", "year", "grade", "class", "level", "السنة", "السنة_الدراسية", "الفرقة", "الصف"]

def _normalize_text(s: str) -> str:
    if s is None: return ""
    s = str(s).strip().lower()
    s = re.sub(r"\s+", "_", s)
    s = s.replace("أ","ا").replace("إ","ا").replace("آ","ا").replace("ة","ه").replace("ـ","")
    s = re.sub(r"[^a-z0-9_\u0600-\u06FF]", "", s)
    return s

def _find_column(columns: list[str], aliases: list[str]) -> str | None:
    norm_map = {c: _normalize_text(c) for c in columns}
    for col, norm in norm_map.items():
        if norm in [_normalize_text(a) for a in aliases]:
            return col
    # Fuzzy: contains
    for col, norm in norm_map.items():
        for a in aliases:
            an = _normalize_text(a)
            if an and (an in norm or norm in an):
                return col
    return None

def parse_dataframe(raw_df: pd.DataFrame, forced_year: str | None = None) -> tuple[pd.DataFrame, dict[str, float], bool, list[str]]:
    """
    Returns: (clean_df, subject_max_map, has_max_row, detected_subjects)
    - Finds header row automatically (row containing id/name)
    - Finds MAX row anywhere (contains MAX / النهاية / العظمى / max)
    - Maps any column names to standard names
    """
    if raw_df is None or raw_df.empty:
        return pd.DataFrame(), {}, False, []
    # 1. Find header row: first row that looks like header
    header_idx = 0
    for i in range(min(5, len(raw_df))):
        row_vals = " ".join([str(x).lower() for x in raw_df.iloc[i].tolist()])
        if any(k in row_vals for k in ["student", "name", "id", "طالب", "اسم", "رقم"]):
            header_idx = i; break
    df = raw_df.copy()
    if header_idx > 0:
        df.columns = df.iloc[header_idx]
        df = df.iloc[header_idx+1:].reset_index(drop=True)
    df.columns = [str(c).strip() for c in df.columns]
    # Drop fully empty columns/rows
    df = df.dropna(axis=1, how="all").dropna(axis=0, how="all").reset_index(drop=True)
    if df.empty: return df, {}, False, []
    # 2. Map ID / Name / Year columns
    cols = list(df.columns)
    id_col = _find_column(cols, ID_ALIASES)
    name_col = _find_column(cols, NAME_ALIASES)
    year_col = _find_column(cols, YEAR_ALIASES)
    rename = {}
    if id_col: rename[id_col] = "student_id"
    if name_col: rename[name_col] = "student_name"
    if year_col: rename[year_col] = "academic_year"
    df = df.rename(columns=rename)
    # 3. Detect MAX row anywhere
    has_max = False
    subject_max_map: dict[str, float] = {}
    reserved = {"student_id", "student_name", "academic_year"}
    subjects = [c for c in df.columns if c not in reserved and "unnamed" not in str(c).lower()]
    # Search for MAX row
    max_row_idx = None
    for idx, row in df.iterrows():
        first_vals = " ".join([str(x).lower() for x in row.tolist()[:3]])
        if "max" in first_vals or "النهاية" in first_vals or "العظمى" in first_vals or "الدرجة" in first_vals:
            max_row_idx = idx; has_max = True; break
    if has_max and max_row_idx is not None:
        max_row = df.loc[max_row_idx]
        for s in subjects:
            try:
                v = float(max_row[s])
                subject_max_map[s] = v if v > 0 else 100.0
            except: subject_max_map[s] = 100.0
        df = df.drop(index=max_row_idx).reset_index(drop=True)
    else:
        for s in subjects: subject_max_map[s] = 100.0
    # 4. Clean student_id / name
    if "student_id" in df.columns:
        df["student_id"] = df["student_id"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True)
        # Keep leading zeros: pad to 6 if numeric
        mask = df["student_id"].str.isdigit()
        df.loc[mask, "student_id"] = df.loc[mask, "student_id"].str.zfill(6)
    if "student_name" in df.columns:
        df["student_name"] = df["student_name"].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
    if forced_year:
        df["academic_year"] = forced_year
    elif "academic_year" in df.columns:
        df["academic_year"] = df["academic_year"].astype(str).str.strip().str.lower()
        # Map Arabic year names
        mapping = {"الاولى":"first_year","الأولى":"first_year","اولى":"first_year","الاولي":"first_year",
                   "الثانية":"second_year","التانية":"second_year","الثالثة":"third_year","التالتة":"third_year",
                   "1":"first_year","2":"second_year","3":"third_year","4":"fourth_year","5":"fifth_year"}
        df["academic_year"] = df["academic_year"].replace(mapping)
    return df, subject_max_map, has_max, subjects

def human_message_for_missing_mark(row_num: int, subject: str) -> str:
    return f"Dear Sir/Madam, there is a small issue in row {row_num}. The mark for {subject} is missing. Could you please kindly check it and upload the file again? Thank you so much for your effort."