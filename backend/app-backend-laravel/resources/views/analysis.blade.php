<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Dashboard Analisis</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/water.css@2/out/water.css" />
  <link rel="stylesheet" href="/css/app.css" />
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    body{ background:#0c2239; color:#e8eef5 }
    .box{ max-width:1200px; margin:20px auto; padding:16px; background:#0f2a46; border-radius:12px; border:1px solid rgba(255,255,255,.08) }
    .cards{ display:grid; grid-template-columns: repeat(auto-fit, minmax(220px,1fr)); gap:12px; }
    .card{ background:#0b1f34; border:1px solid rgba(255,255,255,.06); border-radius:10px; padding:12px; }
    .kv span{ display:block; font-size:12px; color:#9bb2c6 }
    .kv strong{ font-size:22px }
    .charts{ display:grid; grid-template-columns: 1fr 1fr 1fr; gap:16px; }
    @media(max-width:1000px){ .charts{ grid-template-columns: 1fr; } }
    .badge{ display:inline-block; padding:2px 8px; border-radius:999px; font-size:12px }
    .trust-high{ background:#1b5e20; color:#e8f5e9 }
    .trust-med{ background:#f57f17; color:#fff8e1 }
    .trust-low{ background:#b71c1c; color:#ffebee }
  </style>
</head>
<body>
  <div class="box">
    <h2>Dashboard Analisis <small>#{{ $productKey }}</small></h2>
    <div id="meta" class="cards"></div>
    <div class="charts">
      <div class="card"><canvas id="sentChart" height="260"></canvas></div>
      <div class="card"><canvas id="trustHist" height="260"></canvas></div>
      <div class="card"><canvas id="fakePie" height="260"></canvas></div>
      <div class="card" style="grid-column: span 3"><canvas id="fakeHist" height="260"></canvas></div>
    </div>
  </div>
  <script>
    const productKey = @json($productKey);
    const apiBase = '/api/analysis/';
    function badge(cls, text){ return `<span class="badge ${cls}">${text}</span>`; }
    function renderMeta(m){
      const el = document.getElementById('meta');
      el.innerHTML = `
        <div class="card kv"><span>Total Reviews</span><strong>${m.count_reviews||0}</strong></div>
        <div class="card kv"><span>Avg Rating</span><strong>${(m.avg_rating||0).toFixed(2)}/5</strong></div>
        <div class="card kv"><span>Avg Trust (norm)</span><strong>${(m.avg_trust_percent_norm||0).toFixed(2)}%</strong><div>${badge(m.trust_level_class||'', m.trust_level||'')}</div></div>
        <div class="card kv"><span>Fake Rate</span><strong>${((m.fake_rate||0)*100).toFixed(2)}%</strong></div>
      `;
    }
    let charts={}; function destroy(id){ if(charts[id]){ charts[id].destroy(); delete charts[id]; } }
    function renderCharts(m){
      const sentCounts = m.sentiment_counts||{}; const sentLabels = Object.keys(sentCounts), sentVals = Object.values(sentCounts);
      destroy('sent'); charts.sent = new Chart(document.getElementById('sentChart'), {type:'bar', data:{labels:sentLabels, datasets:[{label:'Sentiment', data:sentVals, backgroundColor:'#4e79a7'}]}, options:{plugins:{legend:{display:false}}, scales:{y:{beginAtZero:true}}}});
      const bins = m.trust_hist||[]; destroy('trust'); charts.trust=new Chart(document.getElementById('trustHist'),{type:'bar', data:{labels:['0-10','10-20','20-30','30-40','40-50','50-60','60-70','70-80','80-90','90-100'], datasets:[{label:'Reviews', data:bins, backgroundColor:'#f28e2b'}]}, options:{plugins:{legend:{display:false}}, scales:{y:{beginAtZero:true}}}});
      const fr = m.fake_rate||0, total = m.count_reviews||0, fc = Math.round(fr*total), rc = total-fc; destroy('pie'); charts.pie=new Chart(document.getElementById('fakePie'),{type:'doughnut', data:{labels:['Genuine','Fake'], datasets:[{data:[rc,fc], backgroundColor:['#59a14f','#d62728']}]}, options:{plugins:{legend:{position:'bottom'}}}});
      const fh = m.fake_score_hist||{}; destroy('fh'); charts.fh=new Chart(document.getElementById('fakeHist'), {type:'bar', data:{labels:(fh.bins||[]), datasets:[{label:'Count', data:(fh.counts||[]), backgroundColor:(fh.colors||[])}]}, options:{plugins:{legend:{display:false}}, scales:{y:{beginAtZero:true}}}});
    }
    async function load(){
      const r = await fetch(apiBase + encodeURIComponent(productKey));
      if(!r.ok){ alert('Data not found'); return; }
      const j = await r.json(); const m = j.metrics||{}; renderMeta(m); renderCharts(m);
    }
    load();
  </script>
</body>
</html>
