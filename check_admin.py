from backend.database.firebase import get_db
import sys
email = sys.argv[1] if len(sys.argv) > 1 else 'admin@kawader.edu'
email = email.lower().strip()
db = get_db()
doc = db.collection("admins").document(email).get()
if doc.exists:
    data = doc.to_dict()
    print(f"✅ الإيميل موجود: {email}")
    print(f"Data: {data}")
else:
    print(f"❌ الإيميل مش موجود: {email}")
    print("كل الأدمنز اللي موجودين:")
    for d in db.collection("admins").stream():
        print(" -", d.id, d.to_dict().get("email"), d.to_dict().get("role"))
