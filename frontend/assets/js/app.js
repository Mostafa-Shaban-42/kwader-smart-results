async function lookupResult(){
  const name = document.getElementById('studentName').value.trim();
  const year = document.getElementById('academicYear').value;
  const id = document.getElementById('studentId').value.trim();
  const err = document.getElementById('errorMsg');
  if(!name || !year || !id){ err.textContent = "من فضلك املأ جميع الحقول"; err.classList.remove('hidden'); return; }
  const btn = document.getElementById('viewBtn'); btn.textContent = "جارٍ التحميل..."; btn.disabled = true;
  try {
    const res = await apiPost('/results/lookup', {student_name:name, academic_year:year, student_id:id});
    if(!res.success || !res.data){ err.textContent = res.message || "لم يتم العثور على نتيجة"; err.classList.remove('hidden'); return; }
    err.classList.add('hidden');
    document.getElementById('lookupCard').classList.add('hidden');
    const d = res.data;
    document.getElementById('resultCard').classList.remove('hidden');
    document.getElementById('rName').textContent = d.student_name;
    document.getElementById('rId').textContent = d.student_id;
    document.getElementById('rYear').textContent = d.academic_year;
    document.getElementById('subjectsBody').innerHTML = Object.entries(d.subjects).map(([k,v])=>`<tr><td>${k}</td><td>${v.obtained}</td><td>${v.maximum}</td></tr>`).join('');
    document.getElementById('rTotal').textContent = d.total_obtained + " / " + d.total_maximum;
    document.getElementById('rPct').textContent = d.percentage;
    document.getElementById('rGrade').textContent = d.grade_ar || d.grade;
    document.getElementById('rRank').textContent = d.rank;
    drawSubjectChart(d.subjects);
  } catch(e){ err.textContent = "حدث خطأ في الاتصال بالخادم. حاول مرة أخرى."; err.classList.remove('hidden'); }
  finally { btn.textContent = "عرض النتيجة"; btn.disabled = false; }
}