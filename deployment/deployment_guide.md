# Deployment - Railway + Vercel
1. Firebase: Create project, enable Firestore, create Service Account, copy JSON to Railway Env var GOOGLE_APPLICATION_CREDENTIALS_JSON (never commit).
2. Railway: New Project > Deploy from GitHub > Select repo. It uses Dockerfile. Add env: FIREBASE_PROJECT_ID, GOOGLE_APPLICATION_CREDENTIALS_JSON, JWT_SECRET, FRONTEND_ORIGIN.
3. Vercel: Import Repo > Deploy. It uses vercel.json. Frontend at https://kwader-smart-results-frontend.vercel.app
4. Create Admin once: python backend/create_admin.py admin@kawader.edu YourStrongPassword
5. Put your 4 design images in frontend/assets/images/ as bg-main.jpg, bg-result.jpg, bg-login.jpg, bg-upload.jpg - same design, no difference.
6. Test: GET /api/v1/health, Login, Upload any Excel, Calculate, Publish per year, Student lookup.