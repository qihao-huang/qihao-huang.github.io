"""HTML template for generate_fav.py — tag-centric favorites dashboard."""

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>qihao's 收藏仪表盘 — __TOTAL__ 条</title>
<script>
(function(){
  var m = localStorage.getItem('fav-theme-mode') || 'system';
  if (m === 'light' || m === 'dark') document.documentElement.setAttribute('data-theme', m);
})();
</script>
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
:root{color-scheme:light dark}
:root,:root[data-theme="dark"]{
  --bg:#0f1419;--bg2:#1a2332;--bg3:#243044;--border:#2d3a4f;
  --text:#e8edf4;--muted:#8b9cb3;--accent:#4dabf7;--accent-rgb:77,171,247;
  --chart-text:#e8edf4;--chart-muted:#8b9cb3;--chart-bar:#4dabf7;
  --tag:#51cf66;--method:#ff922b;--folder:#74c0fc;
}
:root[data-theme="light"]{
  --bg:#f4f6f9;--bg2:#ffffff;--bg3:#e9eef4;--border:#d5dde8;
  --text:#1a2332;--muted:#5c6b7f;--accent:#228be6;--accent-rgb:34,139,230;
  --chart-text:#1a2332;--chart-muted:#5c6b7f;--chart-bar:#228be6;
  --tag:#2f9e44;--method:#e8590c;--folder:#1c7ed6;
}
@media (prefers-color-scheme:light){
  :root:not([data-theme="light"]):not([data-theme="dark"]){
    --bg:#f4f6f9;--bg2:#ffffff;--bg3:#e9eef4;--border:#d5dde8;
    --text:#1a2332;--muted:#5c6b7f;--accent:#228be6;--chart-text:#1a2332;--chart-muted:#5c6b7f;
  }
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",sans-serif;font-size:14px;height:100vh;display:flex;flex-direction:column;overflow:hidden}
a{color:var(--accent);text-decoration:none}
.header{background:var(--bg2);border-bottom:1px solid var(--border);padding:12px 20px;display:flex;align-items:center;gap:16px;flex-shrink:0;flex-wrap:wrap}
.header h1{font-size:17px;font-weight:700;white-space:nowrap}
.header h1 span{color:var(--accent)}
.search-wrap{flex:1;max-width:420px;min-width:180px;position:relative}
.search-wrap input{width:100%;background:var(--bg3);border:1px solid var(--border);color:var(--text);padding:8px 12px 8px 34px;border-radius:8px;font-size:13px;outline:none}
.search-wrap input:focus{border-color:var(--accent)}
.search-wrap::before{content:"🔍";position:absolute;left:10px;top:50%;transform:translateY(-50%);opacity:.6}
.header-controls{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-left:auto}
.header-controls select{background:var(--bg3);border:1px solid var(--border);color:var(--text);padding:5px 8px;border-radius:6px;font-size:12px}
.stats{display:flex;gap:12px;font-size:12px;color:var(--muted);align-items:center;flex-wrap:wrap}
.stat-val{color:var(--text);font-weight:600}
.theme-switch{display:flex;gap:2px;background:var(--bg3);border:1px solid var(--border);border-radius:8px;padding:2px}
.theme-btn{padding:4px 8px;border-radius:6px;border:none;background:transparent;color:var(--muted);cursor:pointer;font-size:12px}
.theme-btn.active{background:var(--accent);color:#fff}
.main{flex:1;display:flex;flex-direction:row;overflow:hidden}
.sidebar{width:200px;min-width:160px;max-width:220px;background:var(--bg2);border-right:1px solid var(--border);display:flex;flex-direction:column;flex-shrink:0;overflow:hidden}
.sidebar-title{padding:12px 14px 8px;font-size:11px;font-weight:600;color:var(--muted);flex-shrink:0;border-bottom:1px solid var(--border)}
.sidebar-tags{flex:1;overflow-y:auto;padding:6px 8px 12px}
.sidebar-tag{display:flex;align-items:center;justify-content:space-between;width:100%;padding:7px 10px;border-radius:6px;border:1px solid transparent;background:transparent;color:var(--text);font-size:12px;cursor:pointer;text-align:left;transition:background .12s,border-color .12s,color .12s;font-family:inherit;line-height:1.35}
.sidebar-tag:hover{filter:brightness(1.08)}
.sidebar-tag.selected{font-weight:600}
.sidebar-tag .tag-name{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0;flex:1}
.sidebar-tag .cnt{font-size:10px;color:var(--muted);margin-left:8px;flex-shrink:0}
.sidebar-tag.selected .cnt{color:inherit;opacity:.75}
.sidebar-tag.sidebar-tag-all.selected{background:rgba(var(--accent-rgb),.15);color:var(--accent);border-color:rgba(var(--accent-rgb),.35)}
.sidebar-tag.sidebar-tag-all.selected .cnt{color:var(--accent)}
.main-content{flex:1;display:flex;flex-direction:column;overflow:hidden;min-width:0}
@media(max-width:768px){
  .main{flex-direction:column}
  .sidebar{width:100%;max-width:none;border-right:none;border-bottom:1px solid var(--border);max-height:140px}
  .sidebar-tags{display:flex;flex-wrap:wrap;gap:4px;padding:8px;align-content:flex-start}
  .sidebar-tag{width:auto;flex:0 1 auto;max-width:100%;padding:5px 10px;border:1px solid var(--border);background:var(--bg3);border-radius:999px;font-size:11px}
}
.tabs{display:flex;border-bottom:1px solid var(--border);background:var(--bg2);flex-shrink:0;padding:0 16px}
.tab{padding:10px 16px;font-size:13px;color:var(--muted);cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-1px;white-space:nowrap}
.tab.active{color:var(--accent);border-bottom-color:var(--accent)}
.tab-content{flex:1;overflow:hidden;display:none;flex-direction:column}
.tab-content.active{display:flex}
.chart-stack{display:flex;flex-direction:column;gap:16px;padding:16px 20px;flex:1;overflow:auto}
.chart-card{background:var(--bg2);border:1px solid var(--border);border-radius:10px;padding:8px}
.chart-card-title{font-size:12px;color:var(--muted);padding:4px 8px 0;font-weight:600}
.chart-box{width:100%}
.chart-box.h240{height:240px}
.chart-box.h280{height:280px}
.chart-box.h360{height:360px}
.chart-box.h420{height:420px}
.chart-row{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:900px){.chart-row{grid-template-columns:1fr}}
.list-header{padding:8px 16px;font-size:12px;color:var(--muted);border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center;flex-shrink:0}
.sort-select{background:var(--bg3);border:1px solid var(--border);color:var(--text);padding:3px 8px;border-radius:5px;font-size:11px}
.fav-list{flex:1;overflow-y:auto;padding:12px 16px}
.fav-card{background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:12px 14px;margin-bottom:8px}
.fav-card:hover{border-color:var(--accent)}
.fav-title{font-size:14px;font-weight:600;line-height:1.45;margin-bottom:6px}
.fav-meta{font-size:11px;color:var(--muted);display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:500}
.badge.tag{cursor:pointer;border:1px solid transparent}
.empty-state{text-align:center;padding:60px 20px;color:var(--muted)}
.highlight{background:rgba(77,171,247,.25);border-radius:2px}
.footer-note{font-size:11px;color:var(--muted);padding:8px 20px;border-top:1px solid var(--border);flex-shrink:0}
</style>
</head>
<body>

<header class="header">
  <h1>⭐ <span>收藏仪表盘</span></h1>
  <div class="search-wrap">
    <input id="search" type="text" placeholder="搜索标题、标签、域名…">
  </div>
  <div class="header-controls">
    <div class="theme-switch" id="theme-switch">
      <button class="theme-btn" data-theme-mode="system">自动</button>
      <button class="theme-btn" data-theme-mode="light">☀</button>
      <button class="theme-btn" data-theme-mode="dark">☾</button>
    </div>
    <div class="stats">
      <span>共 <span class="stat-val" id="stat-total">__TOTAL__</span></span>
      <span>标签 <span class="stat-val" id="stat-tags">0</span></span>
      <span id="tagging-mode" style="font-size:10px">__TAGGING__</span>
    </div>
  </div>
</header>

<div class="main">
  <aside class="sidebar" id="tag-sidebar">
    <div class="sidebar-title">标签筛选</div>
    <nav class="sidebar-tags" id="sidebar-tags"></nav>
  </aside>
  <div class="main-content">
  <div class="tabs" id="tabs">
    <div class="tab active" data-tab="timeline">收藏时间线</div>
    <div class="tab" data-tab="list">收藏列表</div>
  </div>

  <div class="tab-content active" id="tab-timeline">
    <div class="chart-stack">
      <div class="chart-row">
        <div class="chart-card">
          <div class="chart-card-title">标签分布 Top 15</div>
          <div class="chart-box h280" id="chart-tags-bar"></div>
        </div>
        <div class="chart-card">
          <div class="chart-card-title">收藏数量（按月）</div>
          <div class="chart-box h280" id="chart-timeline"></div>
        </div>
      </div>
      <div class="chart-card">
        <div class="chart-card-title">标签密度（标签 × 月份）</div>
        <div class="chart-box h420" id="chart-tag-density"></div>
      </div>
    </div>
  </div>

  <div class="tab-content" id="tab-list">
    <div class="list-header">
      <span id="list-count">0 条收藏</span>
      <select class="sort-select" id="sort-select">
        <option value="date-desc">最新收藏</option>
        <option value="date-asc">最早收藏</option>
        <option value="title">标题 A→Z</option>
      </select>
    </div>
    <div class="fav-list" id="fav-list"></div>
  </div>

  <div class="footer-note">生成于 __GENERATED_AT__ · 标签：__TAGGING__</div>
  </div>
</div>

<script>
const DATA = __DATA_JSON__;
const charts = {};
let selectedTags = new Set();
let searchQuery = '';
let activeTab = 'timeline';

function cssVar(name){ return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }
function chartColors(){
  return {
    text: cssVar('--chart-text') || '#e8edf4',
    muted: cssVar('--chart-muted') || '#8b9cb3',
    accent: cssVar('--accent') || '#4dabf7',
    palette: ['#4dabf7','#51cf66','#ff922b','#cc5de8','#20c997','#ffd43b','#74c0fc','#ff6b6b']
  };
}

const TAG_HUES = [207,152,28,280,168,340,12,195,45,260,320,85,0,175,55,310,130,240,20,90];

function isDarkTheme(){
  const t = document.documentElement.getAttribute('data-theme');
  if (t === 'dark') return true;
  if (t === 'light') return false;
  return window.matchMedia('(prefers-color-scheme: dark)').matches;
}

function hashTag(name){
  let h = 0;
  for (let i = 0; i < name.length; i++) {
    h = ((h << 5) - h) + name.charCodeAt(i);
    h |= 0;
  }
  return Math.abs(h);
}

function tagColor(name){
  const hue = TAG_HUES[hashTag(name) % TAG_HUES.length];
  const dark = isDarkTheme();
  if (dark) {
    return {
      bg: 'hsla('+hue+',72%,52%,0.18)',
      bgStrong: 'hsla('+hue+',72%,52%,0.32)',
      text: 'hsl('+hue+',78%,74%)',
      border: 'hsla('+hue+',65%,58%,0.5)',
      solid: 'hsl('+hue+',68%,58%)'
    };
  }
  return {
    bg: 'hsla('+hue+',65%,42%,0.12)',
    bgStrong: 'hsla('+hue+',65%,42%,0.22)',
    text: 'hsl('+hue+',58%,30%)',
    border: 'hsla('+hue+',55%,38%,0.4)',
    solid: 'hsl('+hue+',55%,42%)'
  };
}

function sidebarTagStyle(name, selected){
  const c = tagColor(name);
  if (selected) {
    return 'background:'+c.bgStrong+';color:'+c.text+';border-color:'+c.border;
  }
  return 'border-left:3px solid '+c.border+';padding-left:7px';
}

function monthKey(ts){
  if (!ts) return null;
  const d = new Date(ts * 1000);
  return d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0');
}

function matchesSearch(it, q){
  if (!q) return true;
  const hay = [it.title, it.url, it.domain, (it.tags||[]).join(' ')].join(' ').toLowerCase();
  return hay.includes(q);
}

function searchFilteredItems(){
  const q = searchQuery.trim().toLowerCase();
  return DATA.items.filter(it => matchesSearch(it, q));
}

function filteredItems(){
  const q = searchQuery.trim().toLowerCase();
  return DATA.items.filter(it => {
    if (selectedTags.size) {
      const tags = it.tags || [];
      if (!tags.some(t => selectedTags.has(t))) return false;
    }
    return matchesSearch(it, q);
  });
}

function countTags(items){
  const m = new Map();
  items.forEach(it => (it.tags||[]).forEach(t => m.set(t, (m.get(t)||0)+1)));
  return [...m.entries()].sort((a,b)=>b[1]-a[1]);
}

function updateStats(items){
  document.getElementById('stat-total').textContent = items.length;
  document.getElementById('stat-tags').textContent = countTags(items).length;
  document.getElementById('list-count').textContent = items.length + ' 条收藏';
}

function esc(s){ return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;'); }
function highlight(text, q){
  if (!q) return esc(text);
  const i = String(text).toLowerCase().indexOf(q.toLowerCase());
  if (i < 0) return esc(text);
  return esc(text.slice(0,i))+'<span class="highlight">'+esc(text.slice(i,i+q.length))+'</span>'+esc(text.slice(i+q.length));
}

function switchToTab(tabName){
  activeTab = tabName;
  document.querySelectorAll('.tab').forEach(t=>t.classList.toggle('active', t.dataset.tab===tabName));
  document.querySelectorAll('.tab-content').forEach(p=>p.classList.toggle('active', p.id==='tab-'+tabName));
}

function toggleTag(tag, opts){
  const fromSidebar = opts && opts.fromSidebar;
  if (!tag) {
    selectedTags.clear();
  } else if (fromSidebar) {
    selectedTags.clear();
    selectedTags.add(tag);
    switchToTab('list');
  } else if (selectedTags.has(tag)) {
    selectedTags.delete(tag);
  } else {
    selectedTags.add(tag);
  }
  refresh();
  if (fromSidebar) setTimeout(()=>Object.values(charts).forEach(ch=>{try{ch.resize();}catch(e){}}),50);
}

function renderSidebar(){
  const nav = document.getElementById('sidebar-tags');
  const items = searchFilteredItems();
  const counts = countTags(items);
  let html = `<button type="button" class="sidebar-tag sidebar-tag-all${selectedTags.size?'':' selected'}" data-tag=""><span class="tag-name">全部</span><span class="cnt">${items.length}</span></button>`;
  counts.forEach(([name,cnt])=>{
    const sel = selectedTags.has(name) ? ' selected' : '';
    const style = sidebarTagStyle(name, !!sel);
    html += `<button type="button" class="sidebar-tag${sel}" data-tag="${esc(name)}" style="${style}"><span class="tag-name">${esc(name)}</span><span class="cnt">${cnt}</span></button>`;
  });
  nav.innerHTML = html;
  nav.querySelectorAll('.sidebar-tag').forEach(btn=>{
    btn.onclick = ()=> toggleTag(btn.dataset.tag || '', {fromSidebar:true});
  });
}

function fmtDate(ts){
  if (!ts) return '—';
  const d = new Date(ts * 1000);
  return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');
}

function renderList(items){
  const sort = document.getElementById('sort-select').value;
  const sorted = items.slice();
  if (sort === 'date-desc') sorted.sort((a,b)=>(b.date||0)-(a.date||0));
  else if (sort === 'date-asc') sorted.sort((a,b)=>(a.date||0)-(b.date||0));
  else if (sort === 'title') sorted.sort((a,b)=>a.title.localeCompare(b.title,'zh'));
  const q = searchQuery.trim();
  const list = document.getElementById('fav-list');
  if (!sorted.length){ list.innerHTML = '<div class="empty-state">没有匹配的收藏</div>'; return; }
  list.innerHTML = sorted.map(it=>{
    const tagHtml = (it.tags||[]).map(t=>{
      const c = tagColor(t);
      return `<span class="badge tag" data-tag="${esc(t)}" style="background:${c.bg};color:${c.text};border-color:${c.border}">${highlight(t,q)}</span>`;
    }).join('');
    return `<div class="fav-card">
      <div class="fav-title"><a href="${esc(it.url)}" target="_blank" rel="noopener">${highlight(it.title,q)}</a></div>
      <div class="fav-meta">
        ${tagHtml}
        <span>${esc(it.domain)}</span>
        <span>${fmtDate(it.date)}</span>
      </div></div>`;
  }).join('');
  list.querySelectorAll('.badge.tag').forEach(b=>{
    b.onclick = (e)=>{
      e.preventDefault();
      toggleTag(b.dataset.tag);
    };
  });
}

function baseChartOption(){
  const c = chartColors();
  return { backgroundColor:'transparent', textStyle:{color:c.text}, color:c.palette };
}
function ensureChart(id){
  const el = document.getElementById(id);
  if (!el) return null;
  if (!charts[id]) charts[id] = echarts.init(el);
  return charts[id];
}

function renderTimelineCharts(items){
  const c = chartColors();
  const dated = items.filter(it=>it.date);
  const tagCounts = countTags(items).slice(0,15);
  const byMonth = new Map();
  dated.forEach(it=>{
    const m = monthKey(it.date);
    if (m) byMonth.set(m, (byMonth.get(m)||0)+1);
  });
  const months = [...byMonth.keys()].sort();

  ensureChart('chart-tags-bar').setOption(Object.assign(baseChartOption(), {
    tooltip:{trigger:'axis'},
    grid:{left:120,right:20,top:10,bottom:10},
    xAxis:{type:'value', axisLabel:{color:c.muted}, splitLine:{lineStyle:{color:c.muted,opacity:.12}}},
    yAxis:{type:'category', data:tagCounts.map(x=>x[0]).reverse(), axisLabel:{color:c.muted,fontSize:11}},
    series:[{type:'bar', data:tagCounts.map(x=>x[1]).reverse(), itemStyle:{
      color: p=> tagColor(tagCounts.map(x=>x[0]).reverse()[p.dataIndex]).solid,
      borderRadius:[0,4,4,0]
    }}]
  }), true);

  ensureChart('chart-timeline').setOption(Object.assign(baseChartOption(), {
    tooltip:{trigger:'axis'},
    grid:{left:45,right:15,top:10,bottom:50},
    xAxis:{type:'category', data:months, axisLabel:{color:c.muted,rotate:35,fontSize:10}},
    yAxis:{type:'value', axisLabel:{color:c.muted}, splitLine:{lineStyle:{color:c.muted,opacity:.12}}},
    series:[{type:'line', smooth:true, data:months.map(m=>byMonth.get(m)), areaStyle:{color:'rgba(77,171,247,.15)'}, lineStyle:{color:c.accent,width:2}, itemStyle:{color:c.accent}}]
  }), true);

  const topTags = tagCounts.map(x=>x[0]);
  const matrix = new Map();
  let maxVal = 1;
  dated.forEach(it=>{
    const m = monthKey(it.date);
    if (!m) return;
    (it.tags||[]).forEach(tag=>{
      if (!topTags.includes(tag)) return;
      const k = tag+'\0'+m;
      matrix.set(k, (matrix.get(k)||0)+1);
    });
  });
  const heatData = [];
  topTags.forEach((tag,yi)=>{
    months.forEach((m,xi)=>{
      const v = matrix.get(tag+'\0'+m)||0;
      if (v>maxVal) maxVal=v;
      heatData.push([xi,yi,v]);
    });
  });

  ensureChart('chart-tag-density').setOption(Object.assign(baseChartOption(), {
    tooltip:{position:'top', formatter:p=>{
      return topTags[p.value[1]]+'<br/>'+months[p.value[0]]+'：'+p.value[2]+' 条';
    }},
    grid:{left:130,right:30,top:10,bottom:60},
    xAxis:{type:'category', data:months, axisLabel:{color:c.muted,rotate:35,fontSize:10}},
    yAxis:{type:'category', data:topTags, axisLabel:{color:c.muted,fontSize:11}},
    visualMap:{min:0,max:maxVal,calculable:true,orient:'horizontal',left:'center',bottom:0,
      inRange:{color:['#1a2332','#243044','#4dabf7','#51cf66','#ffd43b']}, textStyle:{color:c.muted}},
    series:[{type:'heatmap', data:heatData, label:{show:false}}]
  }), true);
}

function renderActiveCharts(items){
  if (activeTab === 'timeline') renderTimelineCharts(items);
}

function refresh(){
  const items = filteredItems();
  updateStats(items);
  renderSidebar();
  renderList(items);
  renderActiveCharts(items);
}

function initTheme(){
  const KEY='fav-theme-mode';
  const btns=document.querySelectorAll('.theme-btn');
  function apply(mode){
    if(mode==='system') document.documentElement.removeAttribute('data-theme');
    else document.documentElement.setAttribute('data-theme',mode);
    btns.forEach(b=>b.classList.toggle('active',b.dataset.themeMode===mode));
    localStorage.setItem(KEY,mode);
    Object.values(charts).forEach(ch=>{try{ch.resize();}catch(e){}});
    refresh();
  }
  btns.forEach(b=>b.addEventListener('click',()=>apply(b.dataset.themeMode)));
  apply(localStorage.getItem(KEY)||'system');
}

document.getElementById('search').addEventListener('input',e=>{searchQuery=e.target.value; refresh();});
document.getElementById('sort-select').addEventListener('change',refresh);
document.getElementById('tabs').addEventListener('click',e=>{
  const tab=e.target.closest('.tab'); if(!tab) return;
  switchToTab(tab.dataset.tab);
  refresh();
  setTimeout(()=>Object.values(charts).forEach(ch=>{try{ch.resize();}catch(e){}}),50);
});
window.addEventListener('resize',()=>Object.values(charts).forEach(ch=>{try{ch.resize();}catch(e){}}));

initTheme();
refresh();
</script>
</body>
</html>
"""
