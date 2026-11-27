// Auto-detect environment: localhost -> local backend, otherwise Render backend
const API_BASE = (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
  ? "http://localhost:8000/api/v1"
  : "https://kwader-smart-results-production.up.railway.app/api/v1";
// IMPORTANT: After you create Render service, replace smart-results-backend.onrender.com with your real Render URL

async function apiPost(path, body, token){
  const res = await fetch(API_BASE + path, {method:"POST", headers:{"Content-Type":"application/json", ...(token?{Authorization:"Bearer "+token}:{})}, body: JSON.stringify(body)});
  return res.json();
}
async function apiGet(path, token){
  const res = await fetch(API_BASE + path, {headers: token?{Authorization:"Bearer "+token}:{}});
  return res.json();
}
