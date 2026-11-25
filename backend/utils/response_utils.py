"""Unified API response shape."""
from typing import Any

def success(data: Any = None, message: str = "Success") -> dict:
    return {"success": True, "message": message, "data": data, "error_code": None}

def error_response(error_code: str, message: str) -> dict:
    return {"success": False, "message": message, "data": None, "error_code": error_code}

GENERIC_NOT_FOUND = "لم نتمكن من العثور على نتيجة مطابقة للبيانات المدخلة، يرجى مراجعة البيانات والمحاولة مرة أخرى."
GENERIC_NOT_FOUND_CODE = "RESULT_NOT_AVAILABLE"