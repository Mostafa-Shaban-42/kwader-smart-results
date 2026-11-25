"""
Validation Engine - Single Responsibility: detect problems and explain WHY.
Each issue: row, field, value, code, message_ar, reason_ar, action_ar
Policy: If ANY error exists, whole import is BLOCKED. No partial import.
Supports variable max marks: each subject has its own maximum from MAX row.
"""
from dataclasses import dataclass, asdict
import pandas as pd

REQUIRED_COLUMNS = ["student_id", "student_name", "academic_year"]

@dataclass
class ValidationIssue:
    row: int
    field: str
    value: str
    code: str
    message_ar: str
    reason_ar: str
    action_ar: str
    severity: str = "error"

    def to_dict(self) -> dict:
        return asdict(self)

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    return df

def validate_dataframe(
    df: pd.DataFrame,
    subjects: list[str],
    subject_max_map: dict[str, float] | None = None,
    has_max_row: bool = True
) -> tuple[list[dict], list[dict]]:
    """
    Validate dataframe with per-subject max marks.
    subject_max_map: {"anatomy": 100, "physiology": 50, "practical": 20}
    has_max_row: False -> add warning that defaults 100 were used.
    """
    if subject_max_map is None:
        subject_max_map = {s: 100.0 for s in subjects}

    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []

    # Warn if MAX row missing - admin may have forgotten it
    if not has_max_row:
        warnings.append(ValidationIssue(2, "file", "", "NO_MAX_ROW",
            "تنبيه: لم يتم العثور على صف MAX للدرجات النهائية",
            "السبب: الصف الثاني في الملف لا يبدأ بكلمة MAX. النظام افترض أن كل مادة من 100. لو عندك مادة من 50 أو 20، النسبة هتطلع غلط.",
            "الإجراء: أضف صف ثاني يبدأ بـ MAX في أول خلية، واكتب الدرجة النهائية لكل مادة تحته. مثال: MAX | | | 100 | 50 | 20",
            severity="warning"))

    # Validate MAX row values themselves
    for subj, max_val in subject_max_map.items():
        if max_val <= 0:
            errors.append(ValidationIssue(2, subj, str(max_val), "INVALID_MAX_MARK",
                f"الدرجة النهائية لمادة {subj} غير صحيحة: {max_val}",
                f"السبب: الدرجة النهائية في صف MAX لمادة {subj} هي {max_val}. الدرجة النهائية لازم تكون أكبر من صفر، مفيش مادة نهايتها صفر أو سالب.",
                f"الإجراء: صحح الدرجة النهائية في صف MAX لمادة {subj} إلى رقم صحيح مثل 10 أو 20 أو 50 أو 100."))

    if df.empty:
        errors.append(ValidationIssue(0, "file", "", "EMPTY_FILE",
            "الملف فارغ", "السبب: لا توجد أي صفوف داخل ملف Excel.",
            "الإجراء: تأكد أنك رفعت الملف الصحيح وأنه يحتوي على بيانات."))
        return [e.to_dict() for e in errors], [w.to_dict() for w in warnings]

    df = normalize_columns(df)
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            errors.append(ValidationIssue(1, col, "", "MISSING_COLUMN",
                f"العمود المطلوب غير موجود: {col}",
                f"السبب: ملف Excel لا يحتوي على عمود {col}. بدون هذا العمود لا يمكن التعرف على الطالب.",
                f"الإجراء: أضف عمود {col} في الصف الأول من الملف وأعد الرفع."))
    if errors:
        return [e.to_dict() for e in errors], [w.to_dict() for w in warnings]

    dup_mask = df.duplicated(subset=["student_id", "academic_year"], keep=False)
    if dup_mask.any():
        for idx, row in df[dup_mask].iterrows():
            # +3 because: +1 header, +1 MAX row, +1 zero-index
            excel_row = idx + 3
            errors.append(ValidationIssue(excel_row, "student_id", str(row["student_id"]), "DUPLICATE_ID",
                f"رقم الطالب مكرر: {row['student_id']} في {row['academic_year']}",
                "السبب: نفس رقم الطالب موجود مرتين لنفس السنة. قد يكون الطالب مكتوب مرتين بالخطأ، أو رقم طالب آخر مكتوب غلط.",
                "الإجراء: احذف الصف المكرر أو صحح رقم الطالب، ثم أعد الرفع. لن يتم استيراد أي طالب حتى يتم حل التكرار."))

    for idx, row in df.iterrows():
        # +3: header (1) + MAX row (1) + zero-index (1)
        excel_row = idx + 3
        if row.isna().all():
            warnings.append(ValidationIssue(excel_row, "row", "", "EMPTY_ROW",
                f"صف فارغ في السطر {excel_row} تم تجاهله",
                "السبب: صف فارغ تماماً في Excel، غالباً بسبب ضغطة Enter زيادة.",
                "الإجراء: لا يوجد إجراء. تم تجاهل الصف بأمان ولم يؤثر على أي طالب.",
                severity="warning"))
            continue

        if pd.isna(row.get("student_name")) or str(row.get("student_name")).strip() == "":
            errors.append(ValidationIssue(excel_row, "student_name", "", "MISSING_NAME",
                f"السطر {excel_row}: اسم الطالب مفقود",
                "السبب: خلية اسم الطالب فارغة. بدون الاسم لا يمكن للطالب أن يبحث عن نتيجته لأن البحث يعتمد على الاسم + السنة + رقم الطالب.",
                "الإجراء: اكتب اسم الطالب كاملاً كما في كشوف المدرسة ثم أعد الرفع."))

        if pd.isna(row.get("student_id")) or str(row.get("student_id")).strip() == "":
            errors.append(ValidationIssue(excel_row, "student_id", "", "MISSING_ID",
                f"السطر {excel_row}: رقم الطالب مفقود",
                "السبب: خلية رقم الطالب فارغة. رقم الطالب هو المعرف الفريد، بدونه لا يمكن تمييز الطالب عن زملائه الذين قد يتشابهون في الاسم.",
                "الإجراء: اكتب رقم الطالب كاملاً، مع الحفاظ على الأصفار في البداية مثل 001254."))

        if row.get("academic_year") not in ["first_year", "second_year", "third_year"]:
            errors.append(ValidationIssue(excel_row, "academic_year", str(row.get("academic_year")), "INVALID_YEAR",
                f"السطر {excel_row}: السنة الدراسية غير صحيحة: {row.get('academic_year')}",
                "السبب: السنة الدراسية يجب أن تكون واحدة من ثلاث قيم فقط: first_year أو second_year أو third_year.",
                "الإجراء: غيّر القيمة إلى first_year أو second_year أو third_year ثم أعد الرفع."))

        for subj in subjects:
            if subj not in df.columns:
                continue
            max_mark = subject_max_map.get(subj, 100.0)
            val = row.get(subj)
            if pd.isna(val) or str(val).strip() == "":
                errors.append(ValidationIssue(excel_row, subj, "", "MISSING_MARK",
                    f"السطر {excel_row}: درجة مادة {subj} مفقودة",
                    f"السبب: خلية {subj} فارغة. لا يمكن حساب المجموع الكلي أو النسبة بدون درجة هذه المادة، وأي رقم نفترضه سيكون تزويراً للنتيجة.",
                    f"الإجراء: اكتب درجة الطالب في {subj}، أو اكتب 0 إذا كان غائباً، ثم أعد الرفع."))
                continue
            try:
                num = float(val)
            except (ValueError, TypeError):
                errors.append(ValidationIssue(excel_row, subj, str(val), "NON_NUMERIC_MARK",
                    f"السطر {excel_row}: درجة {subj} ليست رقماً: {val}",
                    "السبب: الخلية تحتوي على نص مثل 'غائب' أو 'A' أو '85+' بدلاً من رقم. النظام لا يستطيع جمع نص مع أرقام.",
                    f"الإجراء: استبدل '{val}' برقم فقط من 0 إلى {max_mark}، أو 0 إذا كان الطالب غائباً."))
                continue
            if num < 0:
                errors.append(ValidationIssue(excel_row, subj, str(val), "NEGATIVE_MARK",
                    f"السطر {excel_row}: درجة سالبة في {subj}: {val}",
                    "السبب: لا توجد درجة سالبة في الواقع. غالباً حدث خطأ كتابة مثل كتابة '-' بدلاً من '+' أو خطأ في نسخ الدرجة.",
                    f"الإجراء: صحح الدرجة إلى رقم بين 0 و {max_mark}."))
            elif num > max_mark:
                errors.append(ValidationIssue(excel_row, subj, str(val), "EXCEEDS_MAX",
                    f"السطر {excel_row}: درجة أكبر من النهاية العظمى في {subj}: {val} / {max_mark}",
                    f"السبب: الدرجة النهائية لمادة {subj} هي {max_mark} كما هو مكتوب في صف MAX. أي رقم أكبر من {max_mark} يعني خطأ كتابة مثل كتابة 85 بدلاً من 8.5، أو جمع درجتين معاً بالخطأ.",
                    f"الإجراء: راجع درجة الطالب الأصلية وصححها إلى رقم بين 0 و {max_mark}."))

    return [e.to_dict() for e in errors], [w.to_dict() for w in warnings]