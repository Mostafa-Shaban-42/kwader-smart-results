"""Atomic publication per year. Each year independent."""
from datetime import datetime
def create_publication(db, batch_id: str, academic_year: str) -> dict:
    ref = db.collection("publications").document()
    pub = {"id": ref.id, "batch_id": batch_id, "academic_year": academic_year, "status": "draft", "created_at": datetime.utcnow(), "published_at": None, "previous_publication_id": None}
    ref.set(pub); return pub

def publish_atomic(db, batch_id: str, records: list[dict], target_year: str | None = None) -> list[str]:
    years = [target_year] if target_year else sorted(set(r["academic_year"] for r in records))
    pub_ids = []
    for year in years:
        prev = get_active_publication(db, year); prev_id = prev["id"] if prev else None
        pub = create_publication(db, batch_id, year); pub["previous_publication_id"] = prev_id
        batch = db.batch()
        for r in [x for x in records if x["academic_year"] == year]:
            ref = db.collection("results").document(f"{year}_{r['student_id']}_{pub['id']}")
            batch.set(ref, {**r, "publication_id": pub["id"]})
        batch.commit()
        db.collection("active_publications").document(year).set({"publication_id": pub["id"], "batch_id": batch_id, "activated_at": datetime.utcnow(), "previous_publication_id": prev_id})
        db.collection("publications").document(pub["id"]).update({"status": "published", "published_at": datetime.utcnow(), "previous_publication_id": prev_id})
        pub_ids.append(pub["id"])
    return pub_ids

def get_active_publication(db, academic_year: str):
    doc = db.collection("active_publications").document(academic_year).get()
    if not doc.exists: return None
    pub_doc = db.collection("publications").document(doc.to_dict()["publication_id"]).get()
    return pub_doc.to_dict() if pub_doc.exists else None

def unpublish(db, publication_id: str) -> dict:
    pub_doc = db.collection("publications").document(publication_id).get()
    if not pub_doc.exists: raise ValueError("Publication not found")
    pub = pub_doc.to_dict(); year = pub["academic_year"]; prev_id = pub.get("previous_publication_id")
    if prev_id:
        db.collection("active_publications").document(year).set({"publication_id": prev_id, "rolled_back_from": publication_id, "activated_at": datetime.utcnow()})
    else:
        db.collection("active_publications").document(year).delete()
    db.collection("publications").document(publication_id).update({"status": "unpublished"})
    return {"id": publication_id, "status": "unpublished", "rolled_back_to": prev_id}

def get_publication_status(db, year: str) -> dict:
    pub = get_active_publication(db, year)
    return {"academic_year": year, "published": bool(pub), "publication_id": pub["id"] if pub else None, "published_at": str(pub.get("published_at")) if pub else None}