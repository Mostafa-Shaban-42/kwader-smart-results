"""Firebase initialization. Supports Render via GOOGLE_APPLICATION_CREDENTIALS_JSON env."""
import os, json
import firebase_admin
from firebase_admin import credentials, firestore
from backend.core.config import settings

_db = None

def get_db():
    """Return Firestore client (singleton)."""
    global _db
    if _db is not None:
        return _db
    if not firebase_admin._apps:
        cred_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        if cred_json:
            # Production on Render: JSON passed as env var, never committed
            cred = credentials.Certificate(json.loads(cred_json))
            firebase_admin.initialize_app(cred, {"projectId": settings.FIREBASE_PROJECT_ID})
        else:
            # Local development
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {"projectId": settings.FIREBASE_PROJECT_ID})
    _db = firestore.client()
    return _db