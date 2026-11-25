# Deployment - Render + Vercel

## 1. Firebase
- Create Firebase project
- Enable Firestore (Native mode)
- Create Service Account -> Download JSON
- Deploy rules: firebase deploy --only firestore:rules

## 2. Render Backend
- Push code to GitHub
- Render > New Web Service > Select repo
- It auto-reads render.yaml
- Add Env Vars in Render Dashboard:
    - FIREBASE_PROJECT_ID = your-project-id
    - GOOGLE_APPLICATION_CREDENTIALS_JSON = {entire service account JSON as one line}
    - JWT_SECRET = long random 32+ chars
    - FRONTEND_ORIGIN = https://your-vercel-domain.vercel.app
- Copy Render URL, e.g. https://smart-results-backend-xxxx.onrender.com
- Paste it in frontend/assets/js/api.js replacing smart-results-backend.onrender.com
- Push again

## 3. Vercel Frontend
- Vercel > Import Repo > Deploy
- Root is auto-detected via vercel.json
- Frontend URL: https://smart-results.vercel.app
- Admin: https://smart-results.vercel.app/admin

## 4. Create Admin (once, from your PC)
python backend/create_admin.py admin@kawader.edu YourStrongPassword123

## 5. Test
- GET https://<render-url>/api/v1/health -> {"success": true}
- Login on /admin
- Upload Excel -> Check validation messages show Reason + Action
- Calculate -> Publish -> Student lookup on homepage

## 6. Backup
- Firestore daily export to Cloud Storage via scheduled export
- Never delete old publications - rollback uses previous_publication_id