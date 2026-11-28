let token=localStorage.getItem('admin_token')||null; let currentBatch=null;

function togglePassword(){
  const p = document.getElementById('password');
  if(!p) return;
  const show = p.type === 'password';
  p.type = show ? 'text' : 'password';
  const btn = document.querySelector('.eye-btn');
  if(btn) btn.style.opacity = show ? '1' : '.45';
  p.focus();
}

function showSection(s){
  const loggedIn = !!token;
  document.getElementById('loginBox').classList.toggle('hidden', loggedIn);
  document.getElementById('uploadBox').classList.toggle('hidden', !loggedIn);
  document.body.className = loggedIn ? 'page-upload' : 'page-login';
  document.body.id = 'pageBody';
  const main = document.getElementById('mainContainer');
  if(main) main.className = loggedIn ? 'container wide' : 'container';
}

async function adminLogin(){
  const email=document.getElementById('email').value.trim(); const password=document.getElementById('password').value;
  if(!email||!password){ alert("Dear Sir/Madam, please kindly enter your email and password."); return; }
  const res=await apiPost('/auth/login',{email,password});
  if(res.success){ token=res.data.token; localStorage.setItem('admin_token',token); showSection('upload'); loadPubStatus(); } else { document.getElementById('loginMsg').textContent=res.message||"Login failed. Please try again."; document.getElementById('loginMsg').classList.remove('hidden'); }
}

async function uploadExcel(){
  const file=document.getElementById('excelFile').files[0]; const year=document.getElementById('uploadYear').value;
  if(!file){ alert("Dear Sir/Madam, please kindly choose an Excel file first."); return; }
  const fd=new FormData(); fd.append('file',file); fd.append('academic_year',year);
  const box=document.getElementById('issuesBox'); box.innerHTML="<p>Dear Sir/Madam, we are kindly checking your file, please wait a moment...</p>";
  try{
    const raw=await fetch(API_BASE+'/imports/upload',{method:'POST',headers:{Authorization:'Bearer '+token},body:fd}); const res=await raw.json();
    if(!res.success){ box.innerHTML=`<div class="issue"><b>${res.message}</b></div>`; return; }
    currentBatch=res.data.batch_id; const errors=res.data.errors||[]; const warnings=res.data.warnings||[];
    let html=`<p>Dear Sir/Madam, we checked ${res.data.total_rows} students. Subjects found: ${res.data.subjects.join(', ')}.</p>`;
    if(res.data.subject_max_map) html+=`<div class="issue"><b>Maximum marks we understood:</b><div>${Object.entries(res.data.subject_max_map).map(([k,v])=>`${k}: ${v}`).join(' | ')}</div><p>Please kindly check if these numbers are correct.</p></div>`;
    html+= [...errors,...warnings].map(i=>`<div class="issue"><b>${i.message}</b><div class="reason">${i.reason}</div><div class="action">${i.action}</div><small>Row ${i.row} - ${i.field}: ${i.value}</small></div>`).join('') || '<p style="color:green">✓ Dear Sir/Madam, no issues found. You can continue to calculate.</p>';
    box.innerHTML=html;
    if(res.data.preview?.length){ let t='<h3>Preview - First 5 Students</h3><table><tr><th>ID</th><th>Name</th>'; res.data.subjects.forEach(s=>t+=`<th>${s}</th>`); t+='</tr>'; res.data.preview.forEach(r=>{ t+=`<tr><td>${r.student_id}</td><td>${r.student_name}</td>`; res.data.subjects.forEach(s=>t+=`<td>${r.subjects[s]?.obtained??'-'}</td>`); t+='</tr>'; }); t+='</table>'; document.getElementById('previewBox').innerHTML=t; }
    document.getElementById('calcBtn').disabled=errors.length>0||!currentBatch;
  }catch(e){ box.innerHTML='<div class="issue"><b>Dear Sir/Madam, there is a connection issue. Please kindly try again.</b></div>'; }
}

async function calculateBatch(){
  if(!currentBatch) return;
  if(!confirm("Dear Sir/Madam, shall we calculate the totals, percentages and ranks now?")) return;
  const res=await apiPost(`/imports/${currentBatch}/calculate`,{},token);
  if(res.success){ alert("Dear Sir/Madam, calculation completed successfully. You can now publish the results."); document.getElementById('publishBtn').disabled=false; } else alert(res.message);
}

async function publishBatch(){
  if(!currentBatch) return;
  if(!confirm("Dear Sir/Madam, are you sure you want to publish? Students will see their results now.")) return;
  const res=await apiPost(`/publications/${currentBatch}/publish`,{},token);
  if(res.success){ alert("Dear Sir/Madam, results published successfully. Thank you so much."); loadPubStatus(); } else alert(res.message);
}

async function loadPubStatus(){
  const res=await apiGet('/publications/status',token);
  if(!res.success) return;
  const data=res.data||{};
  const yearNames={first_year:'First Year',second_year:'Second Year',third_year:'Third Year',fourth_year:'Fourth Year',fifth_year:'Fifth Year'};
  const entries=Object.entries(data);
  const total=entries.length||5;
  const publishedCount=entries.filter(([_,v])=>v && v.published).length;
  const pct=total?Math.round(publishedCount/total*100):0;
  const rows=entries.map(([key,v])=>{
    const isPublished=!!(v && v.published);
    return `<div class="pub-row"><div class="pub-left"><span class="pub-year">${yearNames[key]||key}</span><span class="pub-meta">${isPublished?'Available for students':'Results not published'}</span></div><span class="badge ${isPublished?'badge-published':'badge-draft'}">${isPublished?'Published':'Not Published'}</span></div>`;
  }).join('');
  document.getElementById('pubStatusBox').innerHTML=`<div class="pub-card"><div class="pub-header"><h3>Publication Status</h3><span class="pub-count"><strong>${publishedCount}</strong> of ${total} Published</span></div><div class="pub-progress"><div class="pub-progress-fill" style="width:${pct}%"></div></div><div class="pub-list">${rows}</div></div>`;
}

async function loadAnalytics(){
  const y=document.getElementById('anaYear').value;
  const res=await apiGet(`/analytics/${y}`,token);
  document.getElementById('anaResult').textContent=JSON.stringify(res,null,2);
}

function logout(){
  localStorage.removeItem('admin_token');
  token=null;
  location.reload();
}

if(token){ showSection('upload'); loadPubStatus(); } else showSection('login');