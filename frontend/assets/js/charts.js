let rankChartInstance=null;
function drawRankChart(myPct, avg, highest){
  const ctx=document.getElementById('rankChart'); if(!ctx) return;
  if(rankChartInstance) rankChartInstance.destroy();
  rankChartInstance=new Chart(ctx,{type:'bar',data:{labels:['Your Score','Batch Average','Highest in Batch'],datasets:[{data:[myPct,avg,highest],backgroundColor:['#C9A227','#3A1A63','#8B5CB8']}]},options:{scales:{y:{max:100,beginAtZero:true}},plugins:{legend:{display:false}}}});
}