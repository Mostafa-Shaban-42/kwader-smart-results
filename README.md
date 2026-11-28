# SMART RESULTS - KAWADER NURSING SCHOOL

## Run locally
Backend: uvicorn backend.main:app --reload --port 8000
Frontend: Open frontend/index.html with Live Server

## Deploy
Backend: Railway (uses Dockerfile)
Frontend: Vercel (uses vercel.json)

## Excel - ANY SHAPE ACCEPTED
Smart Parser accepts any column names, any order, any language.
Examples: student_id | Student ID |
Example: student_name | Name | 
MAX row can be anywhere, or missing - system will detect it.
Upload ONE file per year: first_year, second_year, third_year, fourth_year, fifth_year

## Rules
- Ranking: Competition Ranking (1,2,2,4) inside academic_year only
- Grading: 90+ Excellent, 80+ Very Good, 70+ Good, 60+ Pass, <60 Fail
- Publication: Per-year independent, atomic, old version kept for rollback
- Security: No direct Firestore, generic lookup message, rate limit 5/10min
- Messages: Always human, polite, respectful. Never show stack traces.