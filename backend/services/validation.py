"""
Validation with HUMAN, POLITE messages. Never show codes to user.
Each issue has: message (human), reason, action - all respectful.
"""
import pandas as pd
from dataclasses import dataclass, asdict

@dataclass
class ValidationIssue:
    row: int; field: str; value: str; code: str; message: str; reason: str; action: str; severity: str = "error"
    def to_dict(self): return asdict(self)

def validate_dataframe(df, subjects, subject_max_map=None, has_max_row=True, forced_year=None):
    if subject_max_map is None: subject_max_map = {s: 100.0 for s in subjects}
    errors, warnings = [], []
    if not has_max_row:
        warnings.append(ValidationIssue(2, "file", "", "NO_MAX_ROW",
            "Dear Sir/Madam, we could not find the maximum marks row, so we assumed 100 for all subjects.",
            "The file does not contain a row starting with MAX. This is okay, but if you have subjects out of 50 or 20, the percentage may not be correct.",
            "If you have subjects with different maximums, please kindly add a row starting with MAX and upload again. Thank you.", "warning").to_dict())
    if df.empty:
        errors.append(ValidationIssue(0, "file", "", "EMPTY_FILE",
            "Dear Sir/Madam, the file appears to be empty. Could you please check and upload the correct file?",
            "There are no student rows inside the file.", "Please open the file, make sure it contains student data, and try uploading again.", "error").to_dict())
        return errors, warnings
    for col in ["student_id", "student_name"]:
        if col not in df.columns:
            errors.append(ValidationIssue(1, col, "", "MISSING_COLUMN",
                f"Dear Sir/Madam, we could not find the column for {col}. Could you please check the file?",
                f"The file does not contain a column we can understand as {col}.",
                f"Please make sure the file has a column for student name and student ID, with any name you like, and upload again.", "error").to_dict())
    if errors: return errors, warnings
    # Duplicates
    dup = df.duplicated(subset=["student_id", "academic_year"], keep=False)
    if dup.any():
        for idx, row in df[dup].iterrows():
            errors.append(ValidationIssue(idx+3, "student_id", str(row["student_id"]), "DUPLICATE_ID",
                f"Dear Sir/Madam, student number {row['student_id']} appears twice. Could you please kindly review it?",
                "The same student number was found twice for the same year. This may be a small typing mistake.",
                "Please remove the duplicate row or correct the number, then upload again. Thank you so much.", "error").to_dict())
    for idx, row in df.iterrows():
        r = idx + 3
        if row.isna().all():
            warnings.append(ValidationIssue(r, "row", "", "EMPTY_ROW", f"Row {r} is empty, we skipped it safely.", "This is usually an extra Enter press.", "No action needed. Thank you.", "warning").to_dict()); continue
        if pd.isna(row.get("student_name")) or str(row.get("student_name")).strip() in ["", "nan"]:
            errors.append(ValidationIssue(r, "student_name", "", "MISSING_NAME",
                f"Dear Sir/Madam, in row {r}, the student name is missing. Could you please kindly add it?",
                "Without the name, the student cannot search for their result.",
                "Please write the full student name as in school records and upload again. Thank you.", "error").to_dict())
        if pd.isna(row.get("student_id")) or str(row.get("student_id")).strip() in ["", "nan"]:
            errors.append(ValidationIssue(r, "student_id", "", "MISSING_ID",
                f"Dear Sir/Madam, in row {r}, the student number is missing. Could you please kindly add it?",
                "The student number is the unique identifier.",
                "Please write the full student number, keeping leading zeros like 001254, and upload again.", "error").to_dict())
        for subj in subjects:
            max_mark = subject_max_map.get(subj, 100.0)
            val = row.get(subj)
            if pd.isna(val) or str(val).strip() in ["", "nan"]:
                errors.append(ValidationIssue(r, subj, "", "MISSING_MARK",
                    f"Dear Sir/Madam, in row {r}, the mark for {subj} is missing. Could you please kindly check it?",
                    f"The cell for {subj} is empty. We cannot calculate the total without it.",
                    f"Please write the mark for {subj}, or 0 if the student was absent, then upload again. Thank you.", "error").to_dict()); continue
            try: num = float(val)
            except:
                errors.append(ValidationIssue(r, subj, str(val), "NON_NUMERIC_MARK",
                    f"Dear Sir/Madam, in row {r}, the mark for {subj} is '{val}', which is not a number. Could you please kindly correct it?",
                    "The cell contains text instead of a number.", f"Please replace it with a number from 0 to {max_mark}. Thank you.", "error").to_dict()); continue
            if num < 0:
                errors.append(ValidationIssue(r, subj, str(val), "NEGATIVE_MARK",
                    f"Dear Sir/Madam, in row {r}, the mark for {subj} is negative. Could you please kindly review it?",
                    "There is no negative mark in reality, it is likely a small typing mistake.",
                    f"Please correct it to a number between 0 and {max_mark}. Thank you.", "error").to_dict())
            elif num > max_mark:
                errors.append(ValidationIssue(r, subj, str(val), "EXCEEDS_MAX",
                    f"Dear Sir/Madam, in row {r}, the mark for {subj} is {val}, but the maximum is {max_mark}. Could you please kindly check it?",
                    f"The maximum for {subj} is {max_mark}. Any higher number is likely a typing mistake.",
                    f"Please review the original mark and correct it to a number between 0 and {max_mark}. Thank you.", "error").to_dict())
    return errors, warnings