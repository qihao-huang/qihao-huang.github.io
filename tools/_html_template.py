"""Tag-centric HTML template for generate_papers.py."""

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>论文标签库 — __TOTAL__ 篇</title>
<script>
(function(){
  var m = localStorage.getItem('papers-theme-mode') || 'system';
  if (m === 'light' || m === 'dark') document.documentElement.setAttribute('data-theme', m);
})();
</script>
<style>
:root{color-scheme:light dark}
:root,:root[data-theme="dark"]{
  --bg:#0f1419;--bg2:#1a2332;--bg3:#243044;--border:#2d3a4f;
  --text:#e8edf4;--muted:#8b9cb3;--accent:#4dabf7;--accent-rgb:77,171,247;--summary:#a8c5e8;
  --chart-text:#e8edf4;--chart-muted:#8b9cb3;--chart-bar:#4dabf7;--chart-heatmap-diag:#243044;
  --topic:#51cf66;--method:#ff922b;--task:#cc5de8;--modality:#20c997;
  --keyword:#ffd43b;--folder:#74c0fc;--arxiv:#ff6b6b;
}
:root[data-theme="light"]{
  --bg:#f4f6f9;--bg2:#ffffff;--bg3:#e9eef4;--border:#d5dde8;
  --text:#1a2332;--muted:#5c6b7f;--accent:#228be6;--accent-rgb:34,139,230;--summary:#3b5bdb;
  --chart-text:#1a2332;--chart-muted:#5c6b7f;--chart-bar:#228be6;--chart-heatmap-diag:#e9eef4;
  --topic:#2f9e44;--method:#e8590c;--task:#9c36b5;--modality:#0ca678;
  --keyword:#f08c00;--folder:#1c7ed6;--arxiv:#e03131;
}
@media (prefers-color-scheme:light){
  :root:not([data-theme="light"]):not([data-theme="dark"]){
    --bg:#f4f6f9;--bg2:#ffffff;--bg3:#e9eef4;--border:#d5dde8;
    --text:#1a2332;--muted:#5c6b7f;--accent:#228be6;--accent-rgb:34,139,230;--summary:#3b5bdb;
    --chart-text:#1a2332;--chart-muted:#5c6b7f;--chart-bar:#228be6;--chart-heatmap-diag:#e9eef4;
    --topic:#2f9e44;--method:#e8590c;--task:#9c36b5;--modality:#0ca678;
    --keyword:#f08c00;--folder:#1c7ed6;--arxiv:#e03131;
  }
}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC",sans-serif;font-size:14px;height:100vh;display:flex;flex-direction:column;overflow:hidden}
a{color:var(--accent)}
/* Header */
.header{background:var(--bg2);border-bottom:1px solid var(--border);padding:12px 20px;display:flex;align-items:center;gap:16px;flex-shrink:0}
.header h1{font-size:17px;font-weight:700;white-space:nowrap}
.header h1 span{color:var(--accent)}
.search-wrap{flex:1;max-width:480px;position:relative}
.search-wrap input{width:100%;background:var(--bg3);border:1px solid var(--border);color:var(--text);padding:8px 12px 8px 34px;border-radius:8px;font-size:13px;outline:none}
.search-wrap input:focus{border-color:var(--accent)}
.search-wrap::before{content:"🔍";position:absolute;left:10px;top:50%;transform:translateY(-50%);font-size:13px;opacity:.6}
.stats{display:flex;gap:14px;font-size:12px;color:var(--muted);margin-left:auto;white-space:nowrap;align-items:center}
.stat-val{color:var(--text);font-weight:600}
.theme-switch{display:flex;gap:2px;background:var(--bg3);border:1px solid var(--border);border-radius:8px;padding:2px}
.theme-btn{padding:4px 8px;border-radius:6px;border:none;background:transparent;color:var(--muted);cursor:pointer;font-size:12px;line-height:1;transition:background .15s,color .15s}
.theme-btn:hover{color:var(--text)}
.theme-btn.active{background:var(--accent);color:#fff}
.source-tag{font-size:10px;color:var(--muted);margin-left:6px}
.year-filter{padding:8px 14px;border-bottom:1px solid var(--border);flex-shrink:0}
.year-filter select{width:100%;background:var(--bg3);border:1px solid var(--border);color:var(--text);padding:5px 8px;border-radius:6px;font-size:12px}
/* Body layout */
.body{display:flex;flex:1;overflow:hidden}
/* Tag sidebar */
.tag-sidebar{width:280px;min-width:280px;background:var(--bg2);border-right:1px solid var(--border);display:flex;flex-direction:column;overflow:hidden}
.sidebar-head{padding:12px 14px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;flex-shrink:0}
.sidebar-head select{background:var(--bg3);border:1px solid var(--border);color:var(--text);padding:4px 8px;border-radius:6px;font-size:12px}
.filter-mode{display:flex;gap:4px}
.mode-btn{padding:3px 8px;border-radius:5px;border:1px solid var(--border);background:var(--bg3);color:var(--muted);cursor:pointer;font-size:11px}
.mode-btn.active{background:var(--accent);border-color:var(--accent);color:#fff}
.active-tags{padding:8px 14px;border-bottom:1px solid var(--border);min-height:36px;display:flex;flex-wrap:wrap;gap:4px;flex-shrink:0}
.active-tags:empty::after{content:"点击标签筛选论文";color:var(--muted);font-size:11px}
.clear-btn{font-size:11px;color:var(--accent);cursor:pointer;padding:2px 6px;border:none;background:none}
.tag-layers{flex:1;overflow-y:auto;padding:8px 0}
.layer-section{margin-bottom:4px}
.layer-title{padding:6px 14px;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);cursor:pointer;display:flex;align-items:center;gap:6px;user-select:none}
.layer-title::before{content:"▾";font-size:10px;transition:transform .15s}
.layer-section.collapsed .layer-title::before{transform:rotate(-90deg)}
.layer-section.collapsed .layer-tags{display:none}
.layer-tags{padding:2px 8px 6px}
.tag-chip{display:flex;align-items:center;justify-content:space-between;padding:5px 10px;margin:2px 6px;border-radius:6px;cursor:pointer;font-size:12px;transition:background .12s;border:1px solid transparent}
.tag-chip:hover{background:var(--bg3)}
.tag-chip.selected{background:rgba(77,171,247,.15);border-color:var(--accent)}
.tag-chip .cnt{font-size:10px;color:var(--muted);margin-left:6px}
.tag-chip .name{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
/* Main content */
.main{flex:1;display:flex;flex-direction:column;overflow:hidden}
.tabs{display:flex;gap:0;border-bottom:1px solid var(--border);background:var(--bg2);flex-shrink:0;padding:0 16px}
.tab{padding:10px 16px;font-size:13px;color:var(--muted);cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-1px;transition:all .15s}
.tab:hover{color:var(--text)}
.tab.active{color:var(--accent);border-bottom-color:var(--accent)}
.tab-content{flex:1;overflow:hidden;display:none}
.tab-content.active{display:flex;flex-direction:column}
/* Charts */
.chart-area{padding:16px 20px;flex-shrink:0;border-bottom:1px solid var(--border);overflow-x:auto}
.chart-area svg{display:block}
/* Paper list */
.paper-list{flex:1;overflow-y:auto;padding:12px 16px}
.paper-card{background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:12px 14px;margin-bottom:8px;transition:border-color .15s}
.paper-card:hover{border-color:var(--accent)}
.paper-title{font-size:14px;font-weight:600;line-height:1.45;margin-bottom:6px}
.paper-meta{font-size:11px;color:var(--muted);margin-bottom:8px;display:flex;gap:10px;flex-wrap:wrap}
.paper-summary{font-size:13px;color:var(--summary);line-height:1.55;margin-bottom:8px;font-style:normal}
.paper-tags{display:flex;flex-wrap:wrap;gap:4px}
.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:500;cursor:pointer;transition:opacity .12s}
.badge:hover{opacity:.8}
.badge.topic{background:rgba(81,207,102,.15);color:var(--topic)}
.badge.method{background:rgba(255,146,43,.15);color:var(--method)}
.badge.task{background:rgba(204,93,232,.15);color:var(--task)}
.badge.modality{background:rgba(32,201,151,.15);color:var(--modality)}
.badge.keyword{background:rgba(255,212,59,.12);color:var(--keyword)}
.badge.folder{background:rgba(116,192,252,.12);color:var(--folder)}
.badge.arxiv{background:rgba(255,107,107,.12);color:var(--arxiv)}
.badge.lib-auto{background:rgba(77,171,247,.12);color:#74c0fc}
.badge.lib-phys{background:rgba(81,207,102,.12);color:#69db7c}
.list-header{padding:8px 16px;font-size:12px;color:var(--muted);border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center;flex-shrink:0}
.sort-select{background:var(--bg3);border:1px solid var(--border);color:var(--text);padding:3px 8px;border-radius:5px;font-size:11px}
.empty-state{text-align:center;padding:60px 20px;color:var(--muted)}
.empty-state .icon{font-size:40px;margin-bottom:12px}
/* Heatmap */
#heatmap-wrap{padding:16px 20px;overflow:auto;flex:1}
.heatmap-table{border-collapse:collapse;font-size:11px}
.heatmap-table th,.heatmap-table td{padding:4px 6px;text-align:center;min-width:28px}
.heatmap-table th{color:var(--muted);font-weight:500;max-width:80px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.heatmap-cell{border-radius:3px;cursor:pointer;transition:outline .12s,transform .12s;display:flex;align-items:center;justify-content:center;font-size:9px;color:var(--chart-text);line-height:1}
.heatmap-cell:hover{outline:2px solid var(--accent);transform:scale(1.05);z-index:1;position:relative}
.heatmap-cell.empty{background:var(--bg3);border:1px solid var(--border);cursor:default;opacity:.5}
.heatmap-cell.empty:hover{outline:none;transform:none}
.heatmap-caption{font-size:12px;color:var(--muted);margin-bottom:10px;line-height:1.5}
.heatmap-legend{display:flex;align-items:center;gap:8px;margin-top:12px;font-size:11px;color:var(--muted)}
.heatmap-legend-bar{height:10px;width:120px;border-radius:3px;border:1px solid var(--border);background:linear-gradient(to right,rgba(var(--accent-rgb),.08),rgba(var(--accent-rgb),1))}
/* Timeline */
#timeline-wrap{padding:16px 20px;overflow:auto;flex:1}
.highlight{background:rgba(77,171,247,.25);border-radius:2px}
</style>
</head>
<body>

<header class="header">
  <h1>🏷️ <span>论文标签库</span></h1>
  <div class="search-wrap">
    <input id="search" type="text" placeholder="搜索标题、摘要…">
  </div>
  <div class="stats">
    <div class="theme-switch" id="theme-switch" title="主题切换">
      <button class="theme-btn" data-theme-mode="system" title="跟随系统">自动</button>
      <button class="theme-btn" data-theme-mode="light" title="浅色">☀</button>
      <button class="theme-btn" data-theme-mode="dark" title="深色">☾</button>
    </div>
    <span>共 <span class="stat-val" id="stat-total">__TOTAL__</span> 篇</span>
    <span>有日期 <span class="stat-val" id="stat-dates">__WITH_DATE__</span> (<span id="stat-coverage">__COVERAGE__</span>%)</span>
    <span><span class="stat-val" id="stat-tags">__UNIQUE_TAGS__</span> 个标签</span>
    <span>筛选 <span class="stat-val" id="stat-filtered">__TOTAL__</span> 篇</span>
  </div>
</header>

<div class="body">
  <!-- Tag sidebar -->
  <aside class="tag-sidebar">
    <div class="sidebar-head">
      <select id="lib-filter">
        <option value="all">全部库</option>
        <option value="auto_ai">auto_ai (__AUTO_CNT__)</option>
        <option value="physical_ai">physical_ai (__PHYS_CNT__)</option>
      </select>
      <div class="filter-mode">
        <button class="mode-btn active" data-mode="and">AND</button>
        <button class="mode-btn" data-mode="or">OR</button>
      </div>
    </div>
    <div class="active-tags" id="active-tags"></div>
    <div class="year-filter">
      <label style="font-size:11px;color:var(--muted);display:block;margin-bottom:4px">发表年份</label>
      <select id="year-filter"><option value="all">全部年份</option></select>
    </div>
    <div class="tag-layers" id="tag-layers"></div>
  </aside>

  <!-- Main -->
  <div class="main">
    <div class="tabs">
      <div class="tab active" data-tab="list">论文列表</div>
      <div class="tab" data-tab="chart">标签分布</div>
      <div class="tab" data-tab="heatmap">标签共现</div>
      <div class="tab" data-tab="timeline">标签×年份</div>
    </div>

    <!-- List tab -->
    <div class="tab-content active" id="tab-list">
      <div class="list-header">
        <span id="list-info">全部论文</span>
        <select class="sort-select" id="sort-select">
          <option value="relevance">相关度 ↓</option>
          <option value="year-desc" selected>年份 ↓</option>
          <option value="year-asc">年份 ↑</option>
          <option value="title">标题 A-Z</option>
          <option value="tags-desc">标签数 ↓</option>
        </select>
      </div>
      <div class="paper-list" id="paper-list"></div>
    </div>

    <!-- Chart tab -->
    <div class="tab-content" id="tab-chart">
      <div class="chart-area" id="tag-bar-chart"></div>
      <div class="paper-list" id="chart-paper-list" style="flex:1"></div>
    </div>

    <!-- Heatmap tab -->
    <div class="tab-content" id="tab-heatmap">
      <div id="heatmap-wrap"></div>
    </div>

    <!-- Timeline tab -->
    <div class="tab-content" id="tab-timeline">
      <div id="timeline-wrap"></div>
    </div>
  </div>
</div>

<script>
const PAPERS = __PAPERS_JSON__;
const TAG_STATS = __TAG_STATS_JSON__;
const PUB_STATS = __PUB_STATS_JSON__;
const EVOLUTION = __EVOLUTION_JSON__;

const SOURCE_LABELS = {
  pdf:'PDF首页', arxiv_id:'arXiv ID', arxiv_api:'arXiv API',
  crossref:'Crossref', semanticscholar:'Semantic Scholar', unknown:'未知'
};

const LAYER_LABELS = {
  topic:'研究方向', method:'方法', task:'任务', modality:'模态',
  keyword:'关键词', folder:'文件夹', arxiv:'arXiv分类'
};
const LAYER_COLORS = {
  topic:'topic', method:'method', task:'task', modality:'modality',
  keyword:'keyword', folder:'folder', arxiv:'arxiv'
};

const state = {
  query:'', library:'all', year:'all', selectedTags:new Set(), filterMode:'and',
  sort:'year-desc', sortBeforeSearch:null, activeTab:'list', layerFilter:null,
};

const THEME_KEY = 'papers-theme-mode';

function cssVar(name){ return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); }

function heatmapCellColor(value, maxVal){
  if(!value) return null;
  const intensity = value / maxVal;
  return `rgba(${cssVar('--accent-rgb')},${Math.max(0.08, intensity)})`;
}

function heatmapLegendHtml(maxVal){
  return `<div class="heatmap-legend"><span>少</span><div class="heatmap-legend-bar"></div><span>多</span><span style="margin-left:8px">峰值 ${maxVal} 篇</span></div>`;
}

function applyThemeMode(mode){
  const root = document.documentElement;
  if(mode === 'light' || mode === 'dark') root.setAttribute('data-theme', mode);
  else root.removeAttribute('data-theme');
  localStorage.setItem(THEME_KEY, mode);
  document.querySelectorAll('.theme-btn').forEach(btn=>{
    btn.classList.toggle('active', btn.dataset.themeMode === mode);
  });
}

function initTheme(){
  const saved = localStorage.getItem(THEME_KEY) || 'system';
  applyThemeMode(saved);
  document.querySelectorAll('.theme-btn').forEach(btn=>{
    btn.onclick = ()=>{ applyThemeMode(btn.dataset.themeMode); refreshChartsForTheme(); };
  });
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', ()=>{
    if((localStorage.getItem(THEME_KEY)||'system') === 'system') refreshChartsForTheme();
  });
}

function refreshChartsForTheme(){
  const ps = filtered();
  renderTagChart(ps);
  if(state.activeTab==='heatmap') renderHeatmap();
  if(state.activeTab==='timeline') renderTimeline();
}

// ── Utilities ────────────────────────────────────────────────────────────────
function esc(s){return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function tagLayer(tag, paper){
  const t = paper.tags||{};
  for(const [layer,list] of Object.entries(t)){
    if(layer==='all') continue;
    if((list||[]).includes(tag)) return layer;
  }
  return 'topic';
}

// ── Search & relevance ───────────────────────────────────────────────────────
function queryTerms(query){
  return query.toLowerCase().split(/\s+/).filter(Boolean);
}

function scorePaper(p, query){
  if(!query) return 0;
  const q = query.toLowerCase();
  const terms = queryTerms(query);
  const title = (p.title||'').toLowerCase();
  const abstract = (p.abstract||'').toLowerCase();
  const summary = (p.summary_zh||'').toLowerCase();
  const tags = (p.tags?.all||[]).join(' ').toLowerCase();
  let score = 0;
  if(title.includes(q)) score += 100;
  terms.forEach(t=>{ if(title.includes(t)) score += 50; });
  terms.forEach(t=>{ if(abstract.includes(t)) score += 20; });
  terms.forEach(t=>{
    if(summary.includes(t)) score += 5;
    if(tags.includes(t)) score += 3;
  });
  return score;
}

function matchesSearch(p, query){
  if(!query) return true;
  const q = query.toLowerCase();
  const terms = queryTerms(query);
  const title = (p.title||'').toLowerCase();
  const abstract = (p.abstract||'').toLowerCase();
  const summary = (p.summary_zh||'').toLowerCase();
  const tags = (p.tags?.all||[]).join(' ').toLowerCase();
  const inPrimary = s => s.includes(q) || terms.some(t=>s.includes(t));
  if(inPrimary(title) || inPrimary(abstract)) return true;
  if(summary.includes(q) || tags.includes(q)) return true;
  return terms.some(t=>summary.includes(t) || tags.includes(t));
}

function useRelevanceSort(){
  return !!state.query || state.sort==='relevance';
}

function syncSortSelect(){
  document.getElementById('sort-select').value = useRelevanceSort() ? 'relevance' : state.sort;
}

// ── Filtering ────────────────────────────────────────────────────────────────
function filtered(){
  let ps = PAPERS;
  if(state.library!=='all') ps = ps.filter(p=>p.library===state.library);
  if(state.year!=='all') ps = ps.filter(p=>p.pub_year==state.year);
  if(state.query) ps = ps.filter(p=>matchesSearch(p, state.query));
  if(state.selectedTags.size){
    const sel = [...state.selectedTags];
    ps = ps.filter(p=>{
      const tags = new Set(p.tags?.all||[]);
      return state.filterMode==='and'
        ? sel.every(t=>tags.has(t))
        : sel.some(t=>tags.has(t));
    });
  }
  return ps;
}

function sortPapers(ps){
  return [...ps].sort((a,b)=>{
    if(useRelevanceSort()){
      const diff = scorePaper(b, state.query) - scorePaper(a, state.query);
      if(diff) return diff;
      return (b.pub_year||0)-(a.pub_year||0);
    }
    if(state.sort==='year-desc') return (b.pub_year||0)-(a.pub_year||0);
    if(state.sort==='year-asc')  return (a.pub_year||9999)-(b.pub_year||9999);
    if(state.sort==='title')     return (a.title||'').localeCompare(b.title||'');
    if(state.sort==='tags-desc') return (b.tags?.all?.length||0)-(a.tags?.all?.length||0);
    return 0;
  });
}

// ── Tag sidebar ──────────────────────────────────────────────────────────────
function buildTagSidebar(){
  const container = document.getElementById('tag-layers');
  container.innerHTML = '';
  const byLayer = TAG_STATS.by_layer||{};
  const layers = ['topic','method','task','modality','keyword','folder','arxiv'];

  layers.forEach(layer=>{
    const tags = byLayer[layer]||{};
    const entries = Object.entries(tags).sort((a,b)=>b[1]-a[1]);
    if(!entries.length) return;

    const section = document.createElement('div');
    section.className = 'layer-section';
    section.innerHTML = `<div class="layer-title">${LAYER_LABELS[layer]||layer} (${entries.length})</div>`;
    const tagsDiv = document.createElement('div');
    tagsDiv.className = 'layer-tags';

    entries.forEach(([tag,cnt])=>{
      const chip = document.createElement('div');
      chip.className = 'tag-chip'+(state.selectedTags.has(tag)?' selected':'');
      chip.dataset.tag = tag;
      chip.innerHTML = `<span class="name">${esc(tag)}</span><span class="cnt">${cnt}</span>`;
      chip.onclick = ()=>toggleTag(tag);
      tagsDiv.appendChild(chip);
    });

    section.appendChild(tagsDiv);
    section.querySelector('.layer-title').onclick = ()=>section.classList.toggle('collapsed');
    container.appendChild(section);
  });
}

function toggleTag(tag){
  if(state.selectedTags.has(tag)) state.selectedTags.delete(tag);
  else state.selectedTags.add(tag);
  renderActiveTags();
  buildTagSidebar();
  refresh();
}

function renderActiveTags(){
  const el = document.getElementById('active-tags');
  el.innerHTML = '';
  if(!state.selectedTags.size) return;
  const clear = document.createElement('button');
  clear.className = 'clear-btn'; clear.textContent = '清除全部';
  clear.onclick = ()=>{state.selectedTags.clear();renderActiveTags();buildTagSidebar();refresh();};
  el.appendChild(clear);
  state.selectedTags.forEach(tag=>{
    const b = document.createElement('span');
    b.className = 'badge topic'; b.style.cursor='pointer';
    b.textContent = tag + ' ×';
    b.onclick = ()=>toggleTag(tag);
    el.appendChild(b);
  });
}

// ── Paper card ───────────────────────────────────────────────────────────────
function highlightText(text, query){
  if(!query || !text) return esc(text||'');
  const terms = [...new Set([query, ...queryTerms(query)])].filter(Boolean)
    .sort((a,b)=>b.length-a.length);
  let out = esc(text);
  terms.forEach(term=>{
    out = out.replace(
      new RegExp('('+term.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')+')','gi'),
      m=>`<mark class="highlight">${m}</mark>`
    );
  });
  return out;
}

function renderPaperCard(p, highlight=''){
  const tags = p.tags||{};
  const allTags = tags.all||[];
  const tagHtml = allTags.map(t=>{
    const layer = tagLayer(t,p);
    const cls = LAYER_COLORS[layer]||'topic';
    return `<span class="badge ${cls}" data-tag="${esc(t)}" title="${layer}">${esc(t)}</span>`;
  }).join('');
  const libCls = p.library==='auto_ai'?'lib-auto':'lib-phys';
  const yr = `${p.pub_year}${p.pub_month?'-'+String(p.pub_month).padStart(2,'0'):''}`;
  const src = p.pub_date_source ? `<span class="source-tag" title="日期来源">${SOURCE_LABELS[p.pub_date_source]||p.pub_date_source}</span>` : '';
  const arxiv = p.arxiv_id ? `<a href="https://arxiv.org/abs/${p.arxiv_id}" target="_blank">arXiv</a>` : '';
  const title = highlightText(p.title||'', highlight);
  return `<div class="paper-card">
    <div class="paper-title">${title}</div>
    ${p.summary_zh?`<div class="paper-summary">${esc(p.summary_zh)}</div>`:''}
    <div class="paper-meta">
      <span class="badge ${libCls}">${p.library}</span>
      <span>${esc(p.folder||'')}</span>
      <span>${yr}${src}</span>
      ${arxiv}
    </div>
    <div class="paper-tags">${tagHtml||'<span style="color:var(--muted);font-size:11px">无标签</span>'}</div>
  </div>`;
}

function renderPaperList(containerId, ps, limit=200){
  const el = document.getElementById(containerId);
  const sorted = sortPapers(ps);
  if(!sorted.length){
    el.innerHTML = '<div class="empty-state"><div class="icon">🔍</div><div>没有匹配的论文</div></div>';
    return;
  }
  const show = sorted.slice(0, limit);
  el.innerHTML = show.map(p=>renderPaperCard(p, state.query)).join('')
    + (sorted.length>limit?`<div style="text-align:center;padding:12px;color:var(--muted);font-size:12px">还有 ${sorted.length-limit} 篇未显示</div>`:'');
}

// ── Tag bar chart ─────────────────────────────────────────────────────────────
function renderTagChart(ps){
  const el = document.getElementById('tag-bar-chart');
  const counts = {};
  ps.forEach(p=>(p.tags?.all||[]).forEach(t=>{counts[t]=(counts[t]||0)+1;}));
  const data = Object.entries(counts).sort((a,b)=>b[1]-a[1]).slice(0,35);
  if(!data.length){el.innerHTML='';return;}

  const W=Math.max(600, el.offsetWidth||700), rowH=22, ml=200, mr=40;
  const H = data.length*rowH+20;
  const maxV = data[0][1];
  const NS='http://www.w3.org/2000/svg';
  const svg = document.createElementNS(NS,'svg');
  svg.setAttribute('width',W); svg.setAttribute('height',H);

  data.forEach(([tag,v],i)=>{
    const y=i*rowH+4, bw=(v/maxV)*(W-ml-mr);
    const lbl = tag.length>28?tag.slice(0,27)+'…':tag;
    const rect = document.createElementNS(NS,'rect');
    rect.setAttribute('x',ml); rect.setAttribute('y',y); rect.setAttribute('width',bw);
    rect.setAttribute('height',rowH-4); rect.setAttribute('fill',cssVar('--chart-bar')); rect.setAttribute('rx','3');
    rect.style.cursor='pointer';
    rect.onclick=()=>toggleTag(tag);
    svg.appendChild(rect);
    const t1=document.createElementNS(NS,'text');
    t1.setAttribute('x',ml-6); t1.setAttribute('y',y+rowH/2+4);
    t1.setAttribute('text-anchor','end'); t1.setAttribute('fill',cssVar('--chart-text')); t1.setAttribute('font-size','11');
    t1.textContent=lbl; svg.appendChild(t1);
    const t2=document.createElementNS(NS,'text');
    t2.setAttribute('x',ml+bw+4); t2.setAttribute('y',y+rowH/2+4);
    t2.setAttribute('fill',cssVar('--chart-muted')); t2.setAttribute('font-size','10');
    t2.textContent=v; svg.appendChild(t2);
  });
  el.innerHTML=''; el.appendChild(svg);
}

// ── Co-occurrence heatmap ─────────────────────────────────────────────────────
function renderHeatmap(){
  const el = document.getElementById('heatmap-wrap');
  const cooccur = TAG_STATS.cooccur||{};
  const topTags = Object.entries(TAG_STATS.by_tag||{}).sort((a,b)=>b[1]-a[1]).slice(0,18).map(x=>x[0]);

  if(topTags.length<2){el.innerHTML='<div class="empty-state">标签不足</div>';return;}

  const maxCo = Math.max(...topTags.flatMap(t1=>topTags.flatMap(t2=>{
    if(t1===t2) return [];
    return [(cooccur[t1]||{})[t2]||0];
  })),1);
  let html = '<div class="heatmap-caption">Top 18 标签共现矩阵 · 对角线为单标签论文数 · 点击单元格筛选</div>';
  html += '<table class="heatmap-table"><thead><tr><th></th>';
  topTags.forEach(t=>{html+=`<th title="${esc(t)}">${esc(t.slice(0,10))}</th>`;});
  html+='</tr></thead><tbody>';

  topTags.forEach(t1=>{
    html+=`<tr><th title="${esc(t1)}" style="cursor:pointer" data-tag="${esc(t1)}">${esc(t1.slice(0,14))}</th>`;
    topTags.forEach(t2=>{
      const v = t1===t2 ? (TAG_STATS.by_tag[t1]||0) : ((cooccur[t1]||{})[t2]||0);
      const isDiag = t1===t2;
      const color = isDiag ? cssVar('--chart-heatmap-diag') : (heatmapCellColor(v, maxCo)||'transparent');
      const cls = v ? 'heatmap-cell' : 'heatmap-cell empty';
      const label = v && !isDiag && v<=9 ? v : (isDiag && v ? v : '');
      html+=`<td><div class="${cls}" style="background:${color};min-width:26px;height:22px" title="${esc(t1)} × ${esc(t2)}: ${v} 篇" data-tag1="${esc(t1)}" data-tag2="${esc(t2)}" data-diag="${isDiag?1:0}">${label}</div></td>`;
    });
    html+='</tr>';
  });
  html+='</tbody></table>' + heatmapLegendHtml(maxCo);
  el.innerHTML = html;

  el.querySelectorAll('.heatmap-cell:not(.empty)').forEach(cell=>{
    cell.onclick = ()=>{
      const t1 = cell.dataset.tag1, t2 = cell.dataset.tag2;
      state.selectedTags.clear();
      if(cell.dataset.diag==='1') state.selectedTags.add(t1);
      else { state.selectedTags.add(t1); state.selectedTags.add(t2); state.filterMode='and'; }
      document.querySelectorAll('.mode-btn').forEach(b=>b.classList.toggle('active', b.dataset.mode===state.filterMode));
      renderActiveTags(); buildTagSidebar(); refresh();
      state.activeTab='list'; document.querySelector('[data-tab=list]').click();
    };
  });
  el.querySelectorAll('th[data-tag]').forEach(th=>{
    th.onclick = ()=>{ toggleTag(th.dataset.tag); state.activeTab='list'; document.querySelector('[data-tab=list]').click(); };
  });
}

// ── Tag × year heatmap ────────────────────────────────────────────────────────
function renderTimeline(){
  const el = document.getElementById('timeline-wrap');
  const ps = filtered();
  const topN = 18;
  const selTags = state.selectedTags.size ? [...state.selectedTags] :
    Object.entries(TAG_STATS.by_tag||{}).sort((a,b)=>b[1]-a[1]).slice(0, topN).map(x=>x[0]);

  const yearTags = {};
  ps.forEach(p=>{
    const yr = p.pub_year; if(!yr) return;
    if(!yearTags[yr]) yearTags[yr]={};
    (p.tags?.all||[]).forEach(t=>{
      if(selTags.includes(t)) yearTags[yr][t]=(yearTags[yr][t]||0)+1;
    });
  });
  const years = Object.keys(yearTags).sort();
  if(!years.length){el.innerHTML='<div class="empty-state">无发表年份数据</div>';return;}

  const maxV = Math.max(...years.flatMap(y=>selTags.map(t=>yearTags[y][t]||0)),1);
  const caption = state.selectedTags.size
    ? `已选 ${selTags.length} 个标签 × 年份 · 颜色越深论文越多 · 点击单元格按标签+年份筛选`
    : `Top ${selTags.length} 标签 × 年份 · 颜色越深论文越多 · 点击单元格按标签+年份筛选`;

  let html = `<div class="heatmap-caption">${caption}</div>`;
  html += '<table class="heatmap-table"><thead><tr><th></th>';
  years.forEach(yr=>{ html+=`<th title="${yr}">${yr}</th>`; });
  html += '</tr></thead><tbody>';

  selTags.forEach(tag=>{
    html+=`<tr><th title="${esc(tag)}" style="cursor:pointer" data-tag="${esc(tag)}">${esc(tag.slice(0,20))}</th>`;
    years.forEach(yr=>{
      const v = yearTags[yr][tag]||0;
      const color = heatmapCellColor(v, maxV);
      const cls = v ? 'heatmap-cell' : 'heatmap-cell empty';
      const label = v && v<=99 ? v : '';
      html+=`<td><div class="${cls}" style="background:${color||'transparent'};min-width:32px;height:24px" title="${esc(tag)} · ${yr} · ${v} 篇" data-tag="${esc(tag)}" data-year="${yr}">${label}</div></td>`;
    });
    html+='</tr>';
  });
  html+='</tbody></table>' + heatmapLegendHtml(maxV);
  el.innerHTML = html;

  el.querySelectorAll('.heatmap-cell:not(.empty)').forEach(cell=>{
    cell.onclick = ()=>{
      state.selectedTags.clear();
      state.selectedTags.add(cell.dataset.tag);
      state.year = cell.dataset.year;
      document.getElementById('year-filter').value = cell.dataset.year;
      renderActiveTags(); buildTagSidebar(); refresh();
      state.activeTab='list'; document.querySelector('[data-tab=list]').click();
    };
  });
  el.querySelectorAll('th[data-tag]').forEach(th=>{
    th.onclick = ()=>{ toggleTag(th.dataset.tag); };
  });
}

function populateYearFilter(){
  const sel = document.getElementById('year-filter');
  Object.keys(PUB_STATS.by_year||{}).sort((a,b)=>b-a).forEach(y=>{
    const o=document.createElement('option'); o.value=y; o.textContent=y; sel.appendChild(o);
  });
  sel.addEventListener('change', e=>{state.year=e.target.value; refresh();});
}

// ── Refresh all views ─────────────────────────────────────────────────────────
function refresh(){
  const ps = filtered();
  document.getElementById('stat-filtered').textContent = ps.length;
  let listInfo;
  if(state.query){
    listInfo = `搜索「${state.query}」· ${ps.length} 篇 · 相关度↓ 年份↓`;
  } else if(state.selectedTags.size){
    listInfo = `已选 ${state.selectedTags.size} 个标签 · ${ps.length} 篇`;
  } else {
    listInfo = `全部论文 · ${ps.length} 篇`;
  }
  document.getElementById('list-info').textContent = listInfo;
  syncSortSelect();

  renderPaperList('paper-list', ps);
  renderTagChart(ps);
  renderPaperList('chart-paper-list', ps, 50);
  if(state.activeTab==='heatmap') renderHeatmap();
  if(state.activeTab==='timeline') renderTimeline();
}

// ── Event wiring ──────────────────────────────────────────────────────────────
let searchTimer;
document.getElementById('search').addEventListener('input', e=>{
  clearTimeout(searchTimer);
  searchTimer=setTimeout(()=>{state.query=e.target.value.trim();refresh();},200);
});
document.getElementById('lib-filter').addEventListener('change', e=>{
  state.library=e.target.value; buildTagSidebar(); refresh();
});
document.getElementById('sort-select').addEventListener('change', e=>{
  state.sort=e.target.value; refresh();
});
document.querySelectorAll('.mode-btn').forEach(btn=>{
  btn.onclick=()=>{
    state.filterMode=btn.dataset.mode;
    document.querySelectorAll('.mode-btn').forEach(b=>b.classList.toggle('active',b===btn));
    refresh();
  };
});
document.querySelectorAll('.tab').forEach(tab=>{
  tab.onclick=()=>{
    state.activeTab=tab.dataset.tab;
    document.querySelectorAll('.tab').forEach(t=>t.classList.toggle('active',t===tab));
    document.querySelectorAll('.tab-content').forEach(c=>c.classList.remove('active'));
    document.getElementById('tab-'+tab.dataset.tab).classList.add('active');
    if(tab.dataset.tab==='heatmap') renderHeatmap();
    if(tab.dataset.tab==='timeline') renderTimeline();
    if(tab.dataset.tab==='chart') renderTagChart(filtered());
  };
});

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('click', e=>{
  const badge = e.target.closest('.badge[data-tag]');
  if(badge && badge.dataset.tag){ toggleTag(badge.dataset.tag); }
});
buildTagSidebar();
populateYearFilter();
initTheme();
refresh();
</script>
</body>
</html>"""
