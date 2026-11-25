"""Security: name matching, password hashing, JWT, rate limiting."""
import hashlib, hmac, re, time
from datetime import datetime, timedelta
import jwt
from backend.core.config import settings
from backend.core.exceptions import unauthorized

def normalize_name(name: str) -> str:
    """Remove extra spaces, unify spacing, lower case."""
    if not name:
        return ""
    name = str(name).strip()
    name = re.sub(r"\s+", " ", name)
    return name.lower()

def names_match(input_name: str, stored_name: str) -> bool:
    return normalize_name(input_name) == normalize_name(stored_name)

def hash_password(password: str) -> str:
    return hashlib.sha256((password + settings.JWT_SECRET).encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hmac.compare_digest(hash_password(password), hashed)

def create_token(email: str) -> str:
    exp = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": email, "exp": exp, "role": "admin"}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        if payload.get("role") != "admin":
            raise unauthorized()
        return payload
    except Exception:
        raise unauthorized("INVALID_TOKEN", "Invalid or expired token")

_attempts: dict[str, list[float]] = {}

def check_lookup_rate_limit(ip: str) -> None:
    """5 lookup attempts / 10 minutes per IP. Anti-enumeration."""
    if not settings.RATE_LIMIT_ENABLED:
        return
    now = time.time()
    lst = [t for t in _attempts.get(ip, []) if now - t < 600]
    if len(lst) >= 5:
        raise unauthorized("RATE_LIMITED", "Too many attempts. Please try again later.")
    lst.append(now)
    _attempts[ip] = lst