from typing import Any
def success(data: Any = None, message: str = "Success") -> dict: return {"success": True, "message": message, "data": data, "error_code": None}
def error_response(error_code: str, message: str) -> dict: return {"success": False, "message": message, "data": None, "error_code": error_code}
GENERIC_NOT_FOUND = "Dear student, we could not find a result matching the data you entered. Please kindly check your name, seat number and academic year and try again. Thank you."