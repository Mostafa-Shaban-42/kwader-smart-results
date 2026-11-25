"""Run once locally: python backend/create_admin.py admin@kawader.edu StrongPass123"""
import sys
from backend.database.firebase import get_db
from backend.core.security import hash_password

if len(sys.argv) != 3:
    print("Usage: python backend/create_admin.py <email> <password>")
    sys.exit(1)
email = sys.argv[1]
password = sys.argv[2]
db = get_db()
db.collection("admins").document(email.lower()).set({
    "email": email.lower(),
    "password_hash": hash_password(password),
    "role": "admin",
})
print(f"Admin created: {email}")