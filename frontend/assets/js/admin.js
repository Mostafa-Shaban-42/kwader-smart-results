// Admin Dashboard Logic - SMART RESULTS V1.0
// Rules: No duplicate clicks, clear loading states, show REASON + ACTION, preview table

let token = localStorage.getItem('admin_token') || null;
let currentBatch = null;
let currentPreview = [];

// --- Navigation ---
function showSection(section) {
  const uploadBox = document.getElementById('uploadBox');
  const analyticsBox = document.getElementById('analyticsBox');
  const loginBox = document.getElementById('loginBox');
  if (!token) {
    loginBox.classList.remove('hidden');
    uploadBox.classList.add('hidden');
    analyticsBox.classList.add('hidden');
    return;
  }
  loginBox.classList.add('hidden');
  uploadBox.classList.toggle('hidden', section !== 'upload');
  analyticsBox.classList.toggle('hidden', section !== 'analytics');
}

function setButtonLoading(btnId, isLoading, loadingText, normalText) {
  const btn = document.getElementById(btnId);
  if (!btn) return;
  btn.disabled = isLoading;
  btn.textContent = isLoading ? loadingText : normalText;
}

function handleAuthError(res) {
  if (res && (res.error_code === 'INVALID_TOKEN' || res.error_code === 'UNAUTHORIZED')) {
    alert('انتهت الجلسة، سجل دخول مرة أخرى');
    logout();
    return true;
  }
  return false;
}

// --- Auth ---
async function adminLogin() {
  const email = document.getElementById('email').value.trim();
  const password = document.getElementById('password').value;
  if (!email || !password) return alert('اكتب البريد وكلمة المرور');
  setButtonLoading('loginBtn', true, 'جارٍ الدخول...', 'دخول');
  try {
    const res = await apiPost('/auth/login', { email, password });
    if (res.success) {
      token = res.data.token;
      localStorage.setItem('admin_token', token);
      showSection('upload');
    } else {
      alert(res.message || 'فشل الدخول');
    }
  } catch (e) {
    alert('خطأ في الاتصال بالخادم');
  } finally {
    setButtonLoading('loginBtn', false, '', 'دخول');
  }
}

// --- Upload + Preview ---
async function uploadExcel() {
  const fileInput = document.getElementById('excelFile');
  const file = fileInput.files[0];
  if (!file) return alert('اختر ملف Excel أولاً');

  setButtonLoading('uploadBtn', true, 'جارٍ الفحص...', 'رفع وفحص');
  const box = document.getElementById('issuesBox');
  const previewBox = document.getElementById('previewBox');
  box.innerHTML = '<p>جارٍ فحص الملف...</p>';
  previewBox.innerHTML = '';

  try {
    const fd = new FormData();
    fd.append('file', file);
    const raw = await fetch(API_BASE + '/imports/upload', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + token },
      body: fd
    });
    const res = await raw.json();

    if (handleAuthError(res)) return;
    if (!res.success) {
      box.innerHTML = `<div class="issue"><b>${res.message}</b><div class="reason">السبب: ${res.error_code || 'UNKNOWN'}</div></div>`;
      return;
    }

    currentBatch = res.data?.batch_id || null;
    currentPreview = res.data?.preview || [];
    const errors = res.data?.errors || [];
    const warnings = res.data?.warnings || [];
    const maxMap = res.data?.subject_max_map || {};
    const subjects = res.data?.subjects || [];

    let html = '';
    if (Object.keys(maxMap).length) {
      html += `<div class="issue" style="border-color:#9670C8"><b>الدرجات النهائية المكتشفة من صف MAX:</b><div>${Object.entries(maxMap).map(([k, v]) => `${k}: ${v}`).join(' | ')}</div><div class="reason">تأكد أن هذه الأرقام صحيحة قبل النشر. لو رقم غلط، صححه في صف MAX وأعد الرفع.</div></div>`;
    }
    if (!res.data?.has_max_row) {
      html += `<div class="issue"><b>تنبيه: لا يوجد صف MAX</b><div class="reason">السبب: الصف الثاني لا يبدأ بـ MAX. تم افتراض 100 لكل مادة.</div><div class="action">الإجراء: أضف صف MAX لو عندك مواد من 50 أو 20 أو 10.</div></div>`;
    }

    const all = [...errors, ...warnings];
    if (all.length === 0) {
      html += '<p style="color:#027A48;font-weight:700">✓ لا توجد أخطاء - يمكنك المتابعة للحساب</p>';
    } else {
      html += all.map(i => `<div class="issue"><b>${i.message_ar}</b><div class="reason">${i.reason_ar}</div><div class="action">${i.action_ar}</div><small>السطر ${i.row} - الحقل ${i.field} - القيمة: ${i.value}</small></div>`).join('');
    }
    box.innerHTML = html;

    if (currentPreview.length) {
      let table = '<h3>معاينة - أول 5 طلاب</h3><table><thead><tr><th>رقم الطالب</th><th>الاسم</th><th>السنة</th>';
      subjects.forEach(s => { table += `<th>${s} / ${maxMap[s] ?? 100}</th>`; });
      table += '</tr></thead><tbody>';
      currentPreview.forEach(r => {
        table += `<tr><td>${r.student_id}</td><td>${r.student_name}</td><td>${r.academic_year}</td>`;
        subjects.forEach(s => { table += `<td>${r.subjects?.[s]?.obtained ?? '-'}</td>`; });
        table += '</tr>';
      });
      table += '</tbody></table>';
      previewBox.innerHTML = table;
    }

    document.getElementById('uploadResult').textContent = JSON.stringify({
      batch_id: currentBatch,
      total_rows: res.data?.total_rows,
      subject_max_map: maxMap,
      errors_count: errors.length,
      warnings_count: warnings.length
    }, null, 2);

    document.getElementById('calcBtn').disabled = errors.length > 0 || !currentBatch;
    document.getElementById('publishBtn').disabled = true;

  } catch (e) {
    box.innerHTML = '<div class="issue"><b>خطأ في الاتصال</b><div class="reason">السبب: السيرفر مش بيرد أو النت قطع.</div><div class="action">الإجراء: تأكد أن Render شغال وحاول تاني.</div></div>';
  } finally {
    setButtonLoading('uploadBtn', false, '', 'رفع وفحص');
  }
}

// --- Calculate ---
async function calculateBatch() {
  if (!currentBatch) return alert('ارفع ملف صحيح أولاً');
  if (!confirm('حساب النتائج؟ سيتم حساب المجاميع والنسب والترتيب.')) return;
  setButtonLoading('calcBtn', true, 'جارٍ الحساب...', 'حساب النتائج');
  try {
    const res = await apiPost(`/imports/${currentBatch}/calculate`, {}, token);
    if (handleAuthError(res)) return;
    if (res.success) {
      alert('تم الحساب بنجاح\n' + JSON.stringify(res.data?.stats_by_year || {}, null, 2));
      document.getElementById('publishBtn').disabled = false;
    } else {
      alert(res.message || 'فشل الحساب');
    }
  } catch (e) {
    alert('خطأ في الاتصال بالخادم');
  } finally {
    setButtonLoading('calcBtn', false, '', 'حساب النتائج');
  }
}

// --- Publish ---
async function publishBatch() {
  if (!currentBatch) return alert('ارفع واحسب أولاً');
  if (!confirm('هل أنت متأكد من النشر؟ سيتم حفظ النسخة القديمة للرجوع إليها عند الحاجة.')) return;
  setButtonLoading('publishBtn', true, 'جارٍ النشر...', 'نشر النتائج');
  try {
    const res = await apiPost(`/publications/${currentBatch}/publish`, {}, token);
    if (handleAuthError(res)) return;
    if (res.success) alert('تم النشر بنجاح. الطلاب يقدرون يشوفوا نتائجهم الآن.');
    else alert(res.message || 'فشل النشر');
  } catch (e) {
    alert('خطأ في الاتصال بالخادم');
  } finally {
    setButtonLoading('publishBtn', false, '', 'نشر النتائج');
  }
}

// --- Analytics ---
async function loadAnalytics() {
  const y = document.getElementById('anaYear').value;
  const res = await apiGet(`/analytics/${y}`, token);
  if (handleAuthError(res)) return;
  document.getElementById('anaResult').textContent = JSON.stringify(res, null, 2);
}

function logout() {
  localStorage.removeItem('admin_token');
  token = null;
  currentBatch = null;
  location.reload();
}

// Init
if (token) showSection('upload');
else showSection('login');