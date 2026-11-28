"""FastAPI entrypoint. Routing + auth + orchestration only."""
import re
from fastapi import FastAPI, UploadFile, File, Depends, Request, Header, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from backend.core.config import settings, ALLOWED_ORIGINS, YEARS_CONFIG
from backend.core.security import check_lookup_rate_limit, verify_token, create_token, verify_password, names_match
from backend.core.exceptions import bad_request, unauthorized, AppError
from backend.core.years import get_enabled_years
from backend.database.firebase import get_db
from backend.services import excel_processor, validation, statistics, ranking, publication
from backend.services.statistics import motivation_for_student
from backend.utils.file_utils import is_allowed_file, validate_file_size, is_real_excel
from backend.utils.response_utils import success, error_response, GENERIC_NOT_FOUND

app = FastAPI(title=settings.PROJECT_NAME)
app.add_middleware(CORSMiddleware, allow_origins=list(set(ALLOWED_ORIGINS + [settings.FRONTEND_ORIGIN])), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class LoginReq(BaseModel): email: str; password: str
class LookupReq(BaseModel): student_name: str; academic_year: str; student_id: str

def require_admin(authorization: str | None = Header(None)):
    if not authorization or not authorization.startswith("Bearer "): raise unauthorized()
    return verify_token(authorization.replace("Bearer ", ""))

# ---------- تنظيف رقم الجلوس والاسم: 000001 = 1 = ١، عربي = إنجليزي ----------
def normalize_id(v):
    v = str(v or "").strip()
    arabic_digits = "٠١٢٣٤٥٦٧٨٩"
    for i, ch in enumerate(arabic_digits):
        v = v.replace(ch, str(i))
    v = re.sub(r"\D", "", v)
    v = v.lstrip("0") or "0"
    return v

def normalize_name(v):
    v = str(v or "").strip().lower()
    v = re.sub(r"[أإآ]", "ا", v)
    v = v.replace("ة", "ه").replace("ى", "ي")
    v = re.sub(r"[\u064b-\u0652]", "", v)
    v = re.sub(r"\s+", " ", v)
    return v

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    detail = exc.detail if isinstance(exc.detail, dict) else {"error_code": "UNKNOWN", "message": str(exc.detail)}
    return JSONResponse(status_code=exc.status_code, content=error_response(detail.get("error_code", "UNKNOWN"), detail.get("message", "Error")))

@app.get(f"{settings.API_V1_PREFIX}/health")
def health(): return success({"status": "ok", "school": "KAWADER NURSING SCHOOL"})

@app.get(f"{settings.API_V1_PREFIX}/years")
def years(): return success({"years": get_enabled_years()})

@app.post(f"{settings.API_V1_PREFIX}/auth/login")
def login(req: LoginReq):
    db = get_db(); doc = db.collection("admins").document(req.email.lower().strip()).get()
    if not doc.exists or not verify_password(req.password, doc.to_dict().get("password_hash", "")):
        raise unauthorized("INVALID_CREDENTIALS", "Dear Sir/Madam, the email or password is incorrect. Please kindly check and try again.")
    return success({"token": create_token(req.email), "email": req.email})

@app.post(f"{settings.API_V1_PREFIX}/imports/upload")
async def upload(file: UploadFile = File(...), academic_year: str = Form(""), admin=Depends(require_admin)):
    if not is_allowed_file(file.filename): raise bad_request("INVALID_FILE_TYPE", "Dear Sir/Madam, please kindly upload an Excel file (.xlsx or .xls) only. Thank you.")
    content = await file.read()
    try: validate_file_size(len(content), settings.MAX_UPLOAD_SIZE_MB)
    except ValueError: raise bad_request("FILE_TOO_LARGE", "Dear Sir/Madam, the file is too large. Please kindly upload a file smaller than 10 MB.")
    if not is_real_excel(content, file.filename): raise bad_request("FAKE_EXCEL", "Dear Sir/Madam, this file looks like Excel but its content is not a real Excel file. Could you please open it in Excel, save it as .xlsx, and upload again? Thank you.")
    forced_year = academic_year if academic_year in YEARS_CONFIG else None
    try: df, subject_max_map, has_max_row, _ = excel_processor.read_excel(content, forced_year=forced_year)
    except Exception: raise bad_request("CANNOT_READ_EXCEL", "Dear Sir/Madam, we could not read this file. Could you please open it in Excel, save it as .xlsx, and try again? Thank you.")
    subjects = excel_processor.detect_subjects(df)
    if not subjects: raise bad_request("NO_SUBJECTS", "Dear Sir/Madam, we could not find any subjects in this file. Could you please make sure the file contains at least one subject column? Thank you.")
    errors, warnings = validation.validate_dataframe(df, subjects, subject_max_map, has_max_row, forced_year)
    records = excel_processor.df_to_records(df, subjects, subject_max_map) if not errors else []
    db = get_db(); batch_ref = db.collection("import_batches").document()
    batch_ref.set({"id": batch_ref.id, "filename": file.filename, "academic_year": forced_year or "mixed", "subjects": subjects, "subject_max_map": subject_max_map, "has_max_row": has_max_row, "total_rows": len(df), "errors": errors, "warnings": warnings, "status": "uploaded" if not errors else "failed_validation", "records": records})
    return success({"batch_id": batch_ref.id, "academic_year": forced_year, "subjects": subjects, "subject_max_map": subject_max_map, "has_max_row": has_max_row, "total_rows": len(df), "errors": errors, "warnings": warnings, "preview": records[:5]}, message="Dear Sir/Madam, the file was checked successfully. Please kindly review the preview before calculating." if not errors else "Dear Sir/Madam, there are some small issues in the file. Please kindly review them below.")

@app.post(f"{settings.API_V1_PREFIX}/imports/{{batch_id}}/calculate")
def calculate(batch_id: str, admin=Depends(require_admin)):
    db = get_db(); doc = db.collection("import_batches").document(batch_id).get()
    if not doc.exists: raise bad_request("BATCH_NOT_FOUND", "Dear Sir/Madam, this upload was not found. Please kindly upload the file again.")
    data = doc.to_dict()
    if data.get("errors"): raise bad_request("VALIDATION_ERRORS", "Dear Sir/Madam, please kindly fix the issues in the file first, then calculate again. Thank you.")
    calculated = [statistics.calculate_result(dict(r)) for r in data["records"]]
    # الترتيب بيتحسب هنا بدقة من total_obtained تنازلي - مش عشوائي
    ranked = ranking.assign_ranking(calculated)
    stats = {}
    for y in set(r["academic_year"] for r in ranked):
        yr = [r for r in ranked if r["academic_year"] == y]
        stats[y] = {**statistics.year_statistics(yr), "grade_distribution": statistics.grade_distribution(yr)}
    db.collection("import_batches").document(batch_id).update({"records": ranked, "stats_by_year": stats, "status": "calculated"})
    return success({"batch_id": batch_id, "stats_by_year": stats, "count": len(ranked)})

@app.post(f"{settings.API_V1_PREFIX}/publications/{{batch_id}}/publish")
def publish_batch(batch_id: str, admin=Depends(require_admin)):
    db = get_db(); batch = db.collection("import_batches").document(batch_id).get()
    if not batch.exists: raise bad_request("BATCH_NOT_FOUND", "Dear Sir/Madam, this upload was not found.")
    data = batch.to_dict()
    if data.get("status") != "calculated": raise bad_request("NOT_CALCULATED", "Dear Sir/Madam, please kindly calculate the results first, then publish. Thank you.")
    pub_ids = publication.publish_atomic(db, batch_id, data["records"], target_year=data.get("academic_year") if data.get("academic_year") != "mixed" else None)
    db.collection("import_batches").document(batch_id).update({"status": "published", "publication_ids": pub_ids})
    return success({"publication_ids": pub_ids})

@app.get(f"{settings.API_V1_PREFIX}/publications/status")
def pub_status(admin=Depends(require_admin)):
    db = get_db()
    return success({y: publication.get_publication_status(db, y) for y in YEARS_CONFIG})

@app.post(f"{settings.API_V1_PREFIX}/results/lookup")
def lookup(req: LookupReq, request: Request):
    ip = request.client.host if request.client else "unknown"; check_lookup_rate_limit(ip)
    if req.academic_year not in YEARS_CONFIG: return success(None, GENERIC_NOT_FOUND)
    db = get_db(); pub = publication.get_active_publication(db, req.academic_year)
    if not pub: return success(None, GENERIC_NOT_FOUND)

    # البحث برقم الجلوس المتنضف - 1 = 000001 = ١
    search_id = normalize_id(req.student_id)
    search_name = normalize_name(req.student_name)

    # هات كل نتايج السنة دي في الـ publication النشط، وقارن بعد التنظيف
    docs = db.collection("results").where("academic_year", "==", req.academic_year).where("publication_id", "==", pub["id"]).stream()
    candidates = []
    for d in docs:
        data = d.to_dict()
        if normalize_id(data.get("student_id")) == search_id:
            candidates.append(data)

    if not candidates:
        return success(None, GENERIC_NOT_FOUND)

    # لو فيه أكتر من واحد بنفس الرقم، اختار اللي اسمه أقرب
    chosen = candidates[0]
    for data in candidates:
        db_name = normalize_name(data.get("student_name", ""))
        db_name_en = normalize_name(data.get("student_name_en", "") or data.get("english_name", ""))
        # الاسم عربي أو إنجليزي يقبل - ولو الاسم مختلف خالص بنقبل برقم الجلوس لأنه فريد
        if names_match(req.student_name, data.get("student_name", "")) or search_name == db_name or search_name == db_name_en or search_name in db_name or db_name in search_name:
            chosen = data
            break
    data = chosen

    # إحصائيات الدفعة - عشان الترتيب والنسبة يتحسبوا بدقة
    all_docs = db.collection("results").where("academic_year", "==", req.academic_year).where("publication_id", "==", pub["id"]).stream()
    all_results = [x.to_dict() for x in all_docs]
    stats = statistics.year_statistics(all_results)
    # الترتيب الحقيقي من الداتا المخزنة، مش محسوب في الـ Frontend
    real_rank = data.get("rank") or data.get("student_rank") or 0
    total_students = data.get("total_students") or len(all_results)
    motivation = motivation_for_student(real_rank, total_students, data["percentage"])
    return success({"student_name": data["student_name"], "student_id": data["student_id"], "academic_year": data["academic_year"], "subjects": data["subjects"], "total_obtained": data["total_obtained"], "total_maximum": data["total_maximum"], "percentage": round(float(data["percentage"]), 1), "grade": data["grade"], "grade_ar": data.get("grade_ar", ""), "rank": real_rank, "total_students": total_students, "batch_average": stats["average"], "batch_highest": stats["highest"], "motivation": motivation})

@app.get(f"{settings.API_V1_PREFIX}/analytics/{{academic_year}}")
def analytics(academic_year: str, admin=Depends(require_admin)):
    db = get_db(); pub = publication.get_active_publication(db, academic_year)
    if not pub: return success({"count": 0})
    docs = db.collection("results").where("academic_year", "==", academic_year).where("publication_id", "==", pub["id"]).stream()
    results = [d.to_dict() for d in docs]
    return success({**statistics.year_statistics(results), "grade_distribution": statistics.grade_distribution(results)})