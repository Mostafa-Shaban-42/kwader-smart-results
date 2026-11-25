"""FastAPI entrypoint. Only routing + auth + orchestration. No business logic here."""
from fastapi import FastAPI, UploadFile, File, Depends, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from backend.core.config import settings, ACADEMIC_YEARS, ALLOWED_ORIGINS
from backend.core.security import check_lookup_rate_limit, verify_token, create_token, verify_password, names_match
from backend.core.exceptions import bad_request, unauthorized, AppError
from backend.database.firebase import get_db
from backend.services import excel_processor, validation, statistics, ranking, publication
from backend.utils.file_utils import is_allowed_file, validate_file_size, is_real_excel
from backend.utils.response_utils import success, error_response, GENERIC_NOT_FOUND

app = FastAPI(title=settings.PROJECT_NAME)
# CORS: allow Render backend to be called from Vercel frontend
allowed = list(set(ALLOWED_ORIGINS + [settings.FRONTEND_ORIGIN]))
app.add_middleware(CORSMiddleware, allow_origins=allowed, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class LoginReq(BaseModel):
    email: str
    password: str

class LookupReq(BaseModel):
    student_name: str
    academic_year: str
    student_id: str

def require_admin(authorization: str | None = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise unauthorized()
    return verify_token(authorization.replace("Bearer ", ""))

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    detail = exc.detail if isinstance(exc.detail, dict) else {"error_code": "UNKNOWN", "message": str(exc.detail)}
    return JSONResponse(status_code=exc.status_code, content=error_response(detail.get("error_code", "UNKNOWN"), detail.get("message", "Error")))

@app.get(f"{settings.API_V1_PREFIX}/health")
def health():
    return success({"status": "ok", "school": "KAWADER NURSING SCHOOL"})

@app.post(f"{settings.API_V1_PREFIX}/auth/login")
def login(req: LoginReq):
    db = get_db()
    doc = db.collection("admins").document(req.email.lower().strip()).get()
    if not doc.exists:
        raise unauthorized("INVALID_CREDENTIALS", "Invalid credentials")
    if not verify_password(req.password, doc.to_dict().get("password_hash", "")):
        raise unauthorized("INVALID_CREDENTIALS", "Invalid credentials")
    return success({"token": create_token(req.email), "email": req.email})

@app.post(f"{settings.API_V1_PREFIX}/imports/upload")
async def upload(file: UploadFile = File(...), admin=Depends(require_admin)):
    if not is_allowed_file(file.filename):
        raise bad_request("INVALID_FILE_TYPE", "Only .xlsx / .xls allowed")
    content = await file.read()
    try:
        validate_file_size(len(content), settings.MAX_UPLOAD_SIZE_MB)
    except ValueError as e:
        raise bad_request("FILE_TOO_LARGE", str(e))
    if not is_real_excel(content, file.filename):
        raise bad_request("FAKE_EXCEL", "File extension is .xlsx but content is not a real Excel file. Reason: file may be renamed or corrupted. Action: re-export from Excel.")
    try:
        # V2: ONE read returns (df, subject_max_map, has_max_row)
        df, subject_max_map, has_max_row = excel_processor.read_excel(content)
    except Exception:
        raise bad_request("CANNOT_READ_EXCEL", "Cannot read Excel. Reason: file is corrupted or has no sheets. Action: open it in Excel, save as .xlsx, re-upload.")

    subjects = excel_processor.detect_subjects(df)

    if not subjects:
        raise bad_request("NO_SUBJECTS", "No subjects found. Reason: file has only student_id, student_name, academic_year. Action: add at least one subject column + MAX row.")

    errors, warnings = validation.validate_dataframe(df, subjects, subject_max_map, has_max_row)
    records = excel_processor.df_to_records(df, subjects, subject_max_map) if not errors else []

    db = get_db()
    batch_ref = db.collection("import_batches").document()
    batch_ref.set({
        "id": batch_ref.id,
        "filename": file.filename,
        "subjects": subjects,
        "subject_max_map": subject_max_map,
        "has_max_row": has_max_row,
        "total_rows": len(df),
        "errors": errors,
        "warnings": warnings,
        "status": "uploaded" if not errors else "failed_validation",
        "records": records
    })
    return success({
        "batch_id": batch_ref.id,
        "subjects": subjects,
        "subject_max_map": subject_max_map,
        "has_max_row": has_max_row,
        "total_rows": len(df),
        "errors": errors,
        "warnings": warnings,
        "preview": records[:5]
    }, message="Upload validated. Review errors before calculation." if errors else "Upload OK. Review preview then calculate.")

@app.post(f"{settings.API_V1_PREFIX}/imports/{{batch_id}}/calculate")
def calculate(batch_id: str, admin=Depends(require_admin)):
    db = get_db()
    doc = db.collection("import_batches").document(batch_id).get()
    if not doc.exists:
        raise bad_request("BATCH_NOT_FOUND", "Batch not found")
    data = doc.to_dict()
    if data.get("errors"):
        raise bad_request("VALIDATION_ERRORS", "Cannot calculate - fix validation errors first. Each error explains its reason.")
    if not data.get("records"):
        raise bad_request("NO_RECORDS", "No student records to calculate.")
    calculated = [statistics.calculate_result(dict(r)) for r in data["records"]]
    ranked = ranking.assign_ranking(calculated)
    stats_by_year = {}
    for y in ACADEMIC_YEARS:
        yr = [r for r in ranked if r["academic_year"] == y]
        if yr:
            stats_by_year[y] = {**statistics.year_statistics(yr), "grade_distribution": statistics.grade_distribution(yr)}
    db.collection("import_batches").document(batch_id).update({"records": ranked, "stats_by_year": stats_by_year, "status": "calculated"})
    return success({"batch_id": batch_id, "stats_by_year": stats_by_year, "count": len(ranked)})

@app.post(f"{settings.API_V1_PREFIX}/publications/{{batch_id}}/publish")
def publish_batch(batch_id: str, admin=Depends(require_admin)):
    db = get_db()
    batch = db.collection("import_batches").document(batch_id).get()
    if not batch.exists:
        raise bad_request("BATCH_NOT_FOUND", "Batch not found")
    data = batch.to_dict()
    if data.get("status") != "calculated":
        raise bad_request("NOT_CALCULATED", "Calculate first before publishing")
    pub_ids = publication.publish_atomic(db, batch_id, data["records"])
    db.collection("import_batches").document(batch_id).update({"status": "published", "publication_ids": pub_ids})
    return success({"publication_ids": pub_ids})

@app.post(f"{settings.API_V1_PREFIX}/publications/{{publication_id}}/unpublish")
def unpublish_pub(publication_id: str, admin=Depends(require_admin)):
    db = get_db()
    try:
        return success(publication.unpublish(db, publication_id))
    except ValueError as e:
        raise bad_request("PUBLICATION_NOT_FOUND", str(e))

@app.post(f"{settings.API_V1_PREFIX}/results/lookup")
def lookup(req: LookupReq, request: Request):
    ip = request.client.host if request.client else "unknown"
    check_lookup_rate_limit(ip)
    if req.academic_year not in ACADEMIC_YEARS:
        return success(None, GENERIC_NOT_FOUND)
    db = get_db()
    pub = publication.get_active_publication(db, req.academic_year)
    if not pub:
        return success(None, GENERIC_NOT_FOUND)
    docs = db.collection("results").where("student_id", "==", req.student_id.strip()).where("academic_year", "==", req.academic_year).where("publication_id", "==", pub["id"]).limit(1).stream()
    for d in docs:
        data = d.to_dict()
        if not names_match(req.student_name, data.get("student_name", "")):
            return success(None, GENERIC_NOT_FOUND)
        return success({"student_name": data["student_name"], "student_id": data["student_id"], "academic_year": data["academic_year"], "subjects": data["subjects"], "total_obtained": data["total_obtained"], "total_maximum": data["total_maximum"], "percentage": data["percentage"], "grade": data["grade"], "grade_ar": data.get("grade_ar", ""), "rank": data["rank"]})
    return success(None, GENERIC_NOT_FOUND)

@app.get(f"{settings.API_V1_PREFIX}/analytics/{{academic_year}}")
def analytics(academic_year: str, admin=Depends(require_admin)):
    db = get_db()
    pub = publication.get_active_publication(db, academic_year)
    if not pub:
        return success({"count": 0})
    docs = db.collection("results").where("academic_year", "==", academic_year).where("publication_id", "==", pub["id"]).stream()
    results = [d.to_dict() for d in docs]
    return success({**statistics.year_statistics(results), "grade_distribution": statistics.grade_distribution(results)})