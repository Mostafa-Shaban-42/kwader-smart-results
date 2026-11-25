# SMART RESULTS - KAWADER NURSING SCHOOL

## Run locally
Backend: uvicorn backend.main:app --reload --port 8000
Frontend: Open frontend/index.html with Live Server

## Deploy
Backend: Render (uses render.yaml)
Frontend: Vercel (uses vercel.json)

## Excel template
Columns: student_id | student_name | academic_year | <subject1> | <subject2> ...
- student_id as TEXT (preserve 001254)
- academic_year: first_year | second_year | third_year

## Rules
- Ranking: Competition Ranking (1,2,2,4) inside academic_year only
- Grading: 90+ Excellent, 80+ Very Good, 70+ Good, 60+ Pass, <60 Fail
- Publication: Atomic, old version kept for rollback
- Security: No direct Firestore, generic lookup message, rate limit 5/10min