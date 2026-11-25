let subjectChartInstance = null;
function drawSubjectChart(subjects){
  const labels = Object.keys(subjects);
  const data = labels.map(k => subjects[k].obtained);
  const ctx = document.getElementById('subjectChart');
  if(subjectChartInstance) subjectChartInstance.destroy();
  subjectChartInstance = new Chart(ctx, {type:'bar', data:{labels, datasets:[{label:'الدرجة', data, backgroundColor:'#54218C'}]}, options:{scales:{y:{max:100}}}});
}