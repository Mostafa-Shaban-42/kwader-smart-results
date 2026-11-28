from backend.database.firebase import get_db
db = get_db()
print("=== publications ===")
for doc in db.collection("publications").stream():
    print(doc.id, doc.to_dict())
print("\n=== batches ===")
for doc in db.collection("batches").stream():
    d = doc.to_dict()
    print(doc.id, d.get("academic_year"), d.get("status"), "students:", d.get("total_rows"), d.get("created_at"))
print("\n=== results first_year sample ===")
for doc in db.collection("results").where("academic_year", "==", "first_year").limit(3).stream():
    print(doc.id, doc.to_dict())
