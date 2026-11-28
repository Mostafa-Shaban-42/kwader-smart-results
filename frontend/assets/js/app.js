// ---------- تنظيف رقم الجلوس: 000001 = 001 = 1 = ١ ----------
function normalizeId(id) {
  let s = String(id || "").trim();
  const arabicDigits = "٠١٢٣٤٥٦٧٨٩";
  for (let i = 0; i < arabicDigits.length; i++) s = s.split(arabicDigits[i]).join(String(i));
  s = s.replace(/[^0-9]/g, "").replace(/^0+/, "");
  return s || "0";
}

function normalizeName(name) {
  return String(name || "").trim().toLowerCase()
    .replace(/[أإآ]/g, "ا").replace(/ة/g, "ه").replace(/ى/g, "ي")
    .replace(/[\u064B-\u0652]/g, "")
    .replace(/\s+/g, " ");
}

function ordinal(n) {
  n = Number(n) || 0;
  if (n % 100 >= 11 && n % 100 <= 13) return n + "th";
  if (n % 10 === 1) return n + "st";
  if (n % 10 === 2) return n + "nd";
  if (n % 10 === 3) return n + "rd";
  return n + "th";
}

const NICE_SUBJECTS = {
  nursing_fundamentals: "Nursing Fundamentals",
  medical_surgical_nursing: "Medical Surgical Nursing",
  pediatric_nursing: "Pediatric Nursing",
  community_health: "Community Health",
  anatomy: "Anatomy",
  physiology: "Physiology",
  pharmacology: "Pharmacology",
  pathology: "Pathology",
  microbiology: "Microbiology",
  obstetric_nursing: "Obstetric Nursing",
  psychiatric_nursing: "Psychiatric Nursing"
};

function gradeFor(pct) {
  if (pct >= 90) return "Excellent";
  if (pct >= 80) return "Very Good";
  if (pct >= 70) return "Good";
  if (pct >= 60) return "Pass";
  return "Fail";
}

async function lookupResult() {
  const name = document.getElementById('studentName').value.trim();
  const year = document.getElementById('academicYear').value;
  const idRaw = document.getElementById('studentId').value.trim();
  const err = document.getElementById('errorMsg');
  if (!name || !year || !idRaw) { err.textContent = "Please enter your name, seat number and academic year."; err.classList.remove('hidden'); return; }
  const btn = document.getElementById('viewBtn'); btn.textContent = "Loading..."; btn.disabled = true;
  try {
    // بنبعت رقم الجلوس متنضف: 000001 -> 1
    const res = await apiPost('/results/lookup', { student_name: name, academic_year: year, student_id: normalizeId(idRaw) });
    if (!res.success || !res.data) { err.textContent = res.message || "We could not find a result matching the data you entered."; err.classList.remove('hidden'); return; }
    err.classList.add('hidden'); document.getElementById('lookupCard').classList.add('hidden');
    const d = res.data; document.getElementById('resultCard').classList.remove('hidden');
    document.getElementById('rName').textContent = d.student_name;
    document.getElementById('rId').textContent = d.student_id;
    document.getElementById('rYear').textContent = String(d.academic_year).replaceAll("_", " ").replace(/\b\w/g, c => c.toUpperCase());

    // المواد - اسم نضيف + Grade لكل مادة من درجتها، مش Grade عام
    document.getElementById('subjectsBody').innerHTML = Object.entries(d.subjects || {}).map(([k, v], i) => {
      const pct = v.maximum ? (v.obtained / v.maximum * 100) : 0;
      const nice = NICE_SUBJECTS[k] || k.replaceAll("_", " ").replace(/\b\w/g, c => c.toUpperCase());
      return `<tr><td>${i + 1}</td><td>${nice}</td><td>${v.maximum}</td><td>${v.obtained}</td><td>${gradeFor(pct)}</td></tr>`;
    }).join('');

    // النسبة - رقم واحد بس بعد العلامة: 87.3%
    const pct = Number(d.percentage || 0);
    const pct1 = pct.toFixed(1);
    document.getElementById('rPct2').textContent = pct1 + "%";
    document.getElementById('rTotal').textContent = d.total_obtained + " / " + d.total_maximum;
    const gradeEl = document.getElementById('rGradeLabel');
    if (gradeEl) gradeEl.textContent = d.grade || gradeFor(pct);

    // الترتيب - جاي من الـ Backend محسوب بدقة، مش عشوائي
    const rank = Number(d.rank || 0);
    const totalStudents = Number(d.total_students || 0);
    document.getElementById('rRankCircle').textContent = rank ? ordinal(rank) : "-";
    document.getElementById('rRankOut').textContent = totalStudents ? `Out of ${totalStudents}` : "";
    document.getElementById('rRank').textContent = rank || "-";
    document.getElementById('rTotalStudents').textContent = totalStudents || "-";

    // التاج - للعشرة الأوائل بس
    const crown = document.getElementById('crownBadge');
    const circle = document.getElementById('rankCircle');
    if (rank >= 1 && rank <= 10) crown.classList.remove('hidden'); else crown.classList.add('hidden');

    // لون الدايرة حسب الترتيب الحقيقي
    if (rank === 1) { circle.style.borderColor = "#C9A227"; circle.style.background = "#FFF8DC"; }
    else if (rank === 2) { circle.style.borderColor = "#9CA3AF"; circle.style.background = "#F9FAFB"; }
    else if (rank === 3) { circle.style.borderColor = "#CD7F32"; circle.style.background = "#FFF7ED"; }
    else { circle.style.borderColor = "#3B1B5E"; circle.style.background = "#fff"; }

    // الشريط اللي تحت الدايرة
    const m = d.motivation || {};
    const rankBox = document.getElementById('rankBox');
    rankBox.className = "rank-box " + (m.color || "gold");
    if (rank >= 1 && rank <= 10) {
      rankBox.innerHTML = `<div style="font-size:28px">👑</div><h3 style="margin:4px 0">${m.title || "Top 10 Student"}</h3><p>Rank: <b>${ordinal(rank)}</b> out of <b>${totalStudents}</b> Students</p>`;
    } else {
      rankBox.innerHTML = `<div style="font-size:28px">${m.icon || "💜"}</div><h3 style="margin:4px 0">${m.title || ""}</h3><p>Rank: <b>${ordinal(rank)}</b> out of <b>${totalStudents}</b> Students</p>`;
    }
    document.getElementById('motivationText').textContent = m.message || "";
    if (typeof drawRankChart === "function") drawRankChart(d.percentage, d.batch_average, d.batch_highest);
  } catch (e) { err.textContent = "There is a connection issue. Please try again."; err.classList.remove('hidden'); }
  finally { btn.innerHTML = 'View Result <span>→</span>'; btn.disabled = false; }
}