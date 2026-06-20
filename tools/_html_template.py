"""Tag-centric HTML template for generate_papers.py."""

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>qihao's 个人论文阅读备忘录 — __TOTAL__ 篇</title>
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
.paper-list{flex:1;overflow-y:auto;padding:12px 16px;min-height:0}
.paper-list.virtual-scroll-host{position:relative}
.virtual-scroll-spacer{width:100%;pointer-events:none}
.virtual-scroll-viewport{position:absolute;left:0;right:0;top:0;will-change:transform}
.paper-card{background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:12px 14px;margin-bottom:8px;transition:border-color .15s}
.paper-card:hover{border-color:var(--accent)}
.paper-title{font-size:14px;font-weight:600;line-height:1.45;margin-bottom:6px}
.paper-meta{font-size:11px;color:var(--muted);margin-bottom:8px;display:flex;gap:10px;flex-wrap:wrap}
.paper-summary{font-size:13px;color:var(--summary);line-height:1.65;margin-bottom:8px;font-style:normal}
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
.read-tag{font-size:10px;color:var(--accent)}
.alt-copies{font-size:10px;color:var(--muted);cursor:help}
.badge.fail{background:rgba(255,107,107,.15);color:var(--arxiv)}
.badge.fail-warn{background:rgba(255,146,43,.15);color:var(--method)}
.unparsed-path{font-size:11px;color:var(--muted);word-break:break-all;margin-top:4px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
.unparsed-stem{font-size:13px;font-weight:600;line-height:1.4;margin-bottom:4px}
/* Roadmap */
#roadmap-wrap{padding:16px 20px;overflow-y:auto;flex:1}
.roadmap-intro{font-size:13px;color:var(--muted);line-height:1.65;margin-bottom:16px;max-width:720px}
.roadmap-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px;max-width:1100px}
.roadmap-card{background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:14px 16px;transition:border-color .15s}
.roadmap-card:hover{border-color:var(--accent)}
.roadmap-card-head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px;margin-bottom:8px}
.roadmap-card-head h3{font-size:14px;font-weight:600;line-height:1.4;flex:1}
.roadmap-status{display:inline-block;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:600;white-space:nowrap;flex-shrink:0}
.roadmap-status.planned{background:rgba(139,156,179,.15);color:var(--muted)}
.roadmap-status.data-ready{background:rgba(77,171,247,.15);color:var(--accent)}
.roadmap-status.in-progress{background:rgba(255,146,43,.15);color:var(--method)}
.roadmap-status.backend{background:rgba(81,207,102,.15);color:var(--topic)}
.roadmap-desc{font-size:12px;color:var(--muted);line-height:1.65}
.roadmap-foot{margin-top:20px;padding-top:14px;border-top:1px solid var(--border);font-size:11px;color:var(--muted);max-width:720px;line-height:1.6}
</style>
</head>
<body>

<header class="header">
  <h1>🏷️ <span>qihao's 个人论文阅读备忘录</span></h1>
  <div class="search-wrap">
    <input id="search" type="text" placeholder="搜索标题、作者、摘要…">
  </div>
  <div class="stats">
    <div class="theme-switch" id="theme-switch" title="主题切换">
      <button class="theme-btn" data-theme-mode="system" title="跟随系统">自动</button>
      <button class="theme-btn" data-theme-mode="light" title="浅色">☀</button>
      <button class="theme-btn" data-theme-mode="dark" title="深色">☾</button>
    </div>
    <span>共 <span class="stat-val" id="stat-total">__TOTAL__</span> 篇</span>
    <span>近30天阅读 <span class="stat-val" id="stat-recent-read">0</span> 篇</span>
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
      <div class="tab active" data-tab="reading" id="tab-reading-btn">最近阅读</div>
      <div class="tab" data-tab="list">论文列表</div>
      <div class="tab" data-tab="chart">标签分布</div>
      <div class="tab" data-tab="heatmap">标签共现</div>
      <div class="tab" data-tab="timeline">标签×年份</div>
      <div class="tab" data-tab="roadmap">路线图</div>
      <div class="tab" data-tab="unparsed" id="tab-unparsed-btn">未解析 (<span id="tab-unparsed-cnt">__UNPARSED_CNT__</span>)</div>
    </div>

    <!-- Recent reading tab (default) -->
    <div class="tab-content active" id="tab-reading">
      <div class="list-header">
        <span id="reading-info">最近 30 天阅读</span>
      </div>
      <div class="paper-list" id="reading-list"></div>
    </div>

    <!-- List tab -->
    <div class="tab-content" id="tab-list">
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

    <!-- Roadmap tab -->
    <div class="tab-content" id="tab-roadmap">
      <div id="roadmap-wrap">
        <p class="roadmap-intro">以下为论文标签库后续计划增加的功能。状态基于当前代码库：部分后端逻辑或数据已就绪，尚缺前端 Tab 或交互。</p>
        <div class="roadmap-grid">
          <div class="roadmap-card">
            <div class="roadmap-card-head">
              <h3>相似论文图谱</h3>
              <span class="roadmap-status backend">后端已实现</span>
            </div>
            <p class="roadmap-desc">Connected Papers 风格的关联网络：基于 TF-IDF 内容相似度，叠加标签、文件夹与发表年份加权，展示近邻论文与探索路径。</p>
          </div>
          <div class="roadmap-card">
            <div class="roadmap-card-head">
              <h3>兴趣变迁时间线</h3>
              <span class="roadmap-status data-ready">已有数据待接入</span>
            </div>
            <p class="roadmap-desc">按季度汇总研究方向（topic 标签）的论文数量，可视化阅读兴趣随时间的演进曲线；页面已嵌入 EVOLUTION 数据，待独立 Tab 渲染。</p>
          </div>
          <div class="roadmap-card">
            <div class="roadmap-card-head">
              <h3>LLM 智能中文摘要</h3>
              <span class="roadmap-status in-progress">进行中</span>
            </div>
            <p class="roadmap-desc">两档策略：规则摘要质量足够时跳过 LLM；其余走 gpt-4o-mini 生成并缓存至 .papers_cache.json。默认构建零 API 调用；<code>--llm-summary</code> 增量补全，sync 脚本在 OPENAI_API_KEY 存在时自动启用。</p>
          </div>
          <div class="roadmap-card">
            <div class="roadmap-card-head">
              <h3>标签体系与校验增强</h3>
              <span class="roadmap-status in-progress">进行中</span>
            </div>
            <p class="roadmap-desc">完善 taxonomy 分类、修复误标与 uncategorized 论文，在 UI 中展示 validation flags 与 needs_review 标记，支持批量复核。</p>
          </div>
          <div class="roadmap-card">
            <div class="roadmap-card-head">
              <h3>历史快照对比</h3>
              <span class="roadmap-status data-ready">已有数据待接入</span>
            </div>
            <p class="roadmap-desc">利用每日快照（snapshots/history.json）对比库规模、方向分布与需复核数量的变化，追踪知识库增长轨迹。</p>
          </div>
          <div class="roadmap-card">
            <div class="roadmap-card-head">
              <h3>发表年份全景</h3>
              <span class="roadmap-status data-ready">已有数据待接入</span>
            </div>
            <p class="roadmap-desc">独立于「标签×年份」的发表时间分布视图，展示各年论文入库量、日期来源覆盖率，辅助发现缺失元数据的年份段。</p>
          </div>
          <div class="roadmap-card">
            <div class="roadmap-card-head">
              <h3>阅读笔记与批注</h3>
              <span class="roadmap-status planned">规划中</span>
            </div>
            <p class="roadmap-desc">关联 PDF 阅读器批注或独立 Markdown 笔记，在论文卡片中展示个人阅读心得；当前仅通过 mtime 推断最近阅读。</p>
          </div>
          <div class="roadmap-card">
            <div class="roadmap-card-head">
              <h3>筛选结果导出</h3>
              <span class="roadmap-status planned">规划中</span>
            </div>
            <p class="roadmap-desc">将当前标签筛选、搜索结果的论文列表导出为 BibTeX、CSV 或 Markdown，便于引用管理与分享。</p>
          </div>
          <div class="roadmap-card">
            <div class="roadmap-card-head">
              <h3>公开发布模式</h3>
              <span class="roadmap-status backend">已有基础</span>
            </div>
            <p class="roadmap-desc">生成不含阅读时间戳的公开版 HTML（--public 构建选项已支持）；后续可在 UI 提供一键切换或独立发布入口。</p>
          </div>
        </div>
        <p class="roadmap-foot">本页内容为静态路线图，随开发进度更新。如有优先级建议，可在 generate_papers.py 或 _html_template.py 中直接修改。</p>
      </div>
    </div>

    <!-- Unparsed tab -->
    <div class="tab-content" id="tab-unparsed">
      <div class="list-header">
        <span id="unparsed-info">未解析文件 · __UNPARSED_CNT__ 个</span>
        <select class="sort-select" id="unparsed-reason-filter">
          <option value="all">全部原因</option>
        </select>
      </div>
      <div class="paper-list" id="unparsed-list"></div>
    </div>
  </div>
</div>

<script>
const PAPERS = __PAPERS_JSON__;
const UNPARSED = __UNPARSED_JSON__;
const TAG_STATS = __TAG_STATS_JSON__;
const PUB_STATS = __PUB_STATS_JSON__;
const EVOLUTION = __EVOLUTION_JSON__;
const HAS_READING = __HAS_READING__;

// 阅读判定：编辑时间(mtime) 明显晚于下载时间(birthtime)，且在近 30 天内
const READ_EDIT_THRESHOLD = 120;
const READ_WINDOW_SEC = 30 * 24 * 3600;

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

const UNPARSED_REASON_LABELS = {
  no_pub_date:'缺少发表年份',
  duplicate:'重复副本',
  read_error:'无法读取',
  excluded:'已排除',
  empty_file:'空文件',
  course_material:'课件/教程',
  junk_title_course_notes:'垃圾标题·课件',
  cn_tutorial_no_abstract:'中文教程·无摘要',
  course_slides_no_abstract:'课件·无摘要',
  numbered_slides:'编号幻灯片',
  tutorial_slides:'教程幻灯片',
  slides_prefix:'Slides 前缀',
  slides_suffix:'Slides 后缀',
  presentation_deck:'演示文稿',
  tutorial_deck:'教程 deck',
  lecture_deck:'讲座 deck',
  slides_deck:'幻灯片',
  valse_talk:'VALSE 报告',
  intro_slides:'介绍幻灯片',
};

function unparsedReasonLabel(reason){
  if(!reason) return '未知';
  if(UNPARSED_REASON_LABELS[reason]) return UNPARSED_REASON_LABELS[reason];
  if(reason.startsWith('dir:')) return '排除目录 · ' + reason.slice(4);
  return reason;
}

function unparsedReasonClass(reason){
  if(reason === 'no_pub_date' || reason === 'read_error') return 'fail';
  if(reason === 'duplicate') return 'fail-warn';
  return 'fail';
}

const state = {
  query:'', library:'all', year:'all', selectedTags:new Set(), filterMode:'and',
  sort:'year-desc', sortBeforeSearch:null, activeTab:'reading', layerFilter:null,
  unparsedReason:'all',
};

const THEME_KEY = 'papers-theme-mode';

function cssVar(name){
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function fmtTs(ts){
  if(!ts) return '';
  const d = new Date(ts*1000);
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
}

function isEditedAfterDownload(p){
  if(!p.mtime || !p.birthtime) return false;
  return p.mtime > p.birthtime + READ_EDIT_THRESHOLD;
}

function isRecentlyRead(p, windowSec=READ_WINDOW_SEC){
  if(!isEditedAfterDownload(p)) return false;
  const now = Date.now()/1000;
  return p.mtime >= now - windowSec;
}

function recentReadingPapers(windowSec=READ_WINDOW_SEC){
  let ps = PAPERS.filter(p=>isRecentlyRead(p, windowSec));
  if(state.library!=='all') ps = ps.filter(p=>p.library===state.library);
  return ps.sort((a,b)=>(b.mtime||0)-(a.mtime||0));
}

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

function authorsText(p){
  const a = p.authors;
  if(!a) return '';
  return Array.isArray(a) ? a.join(', ') : String(a);
}

function searchableFields(p){
  const authors = authorsText(p).toLowerCase();
  return {
    title: (p.title||'').toLowerCase(),
    authors,
    abstract: (p.abstract||'').toLowerCase(),
    summary: (p.summary_zh||'').toLowerCase(),
    tags: (p.tags?.all||[]).join(' ').toLowerCase(),
  };
}

function searchHaystack(fields){
  return [fields.title, fields.authors, fields.abstract, fields.summary, fields.tags]
    .filter(Boolean).join(' ');
}

function levDistance(a, b){
  if(a === b) return 0;
  if(!a.length) return b.length;
  if(!b.length) return a.length;
  const dp = Array.from({length: a.length + 1}, (_, i) => [i]);
  for(let j = 1; j <= b.length; j++) dp[0][j] = j;
  for(let i = 1; i <= a.length; i++){
    for(let j = 1; j <= b.length; j++){
      const cost = a[i-1] === b[j-1] ? 0 : 1;
      dp[i][j] = Math.min(dp[i-1][j] + 1, dp[i][j-1] + 1, dp[i-1][j-1] + cost);
    }
  }
  return dp[a.length][b.length];
}

function termMatches(term, text){
  if(!term) return true;
  const t = term.toLowerCase();
  if(!text) return false;
  if(text.includes(t)) return true;
  const tokens = text.split(/[\s,;·、]+/).filter(Boolean);
  if(t.length >= 2 && tokens.some(tok => tok.startsWith(t))) return true;
  if(t.length >= 4){
    return tokens.some(tok =>
      tok.length >= t.length - 1 && tok.length <= t.length + 2 &&
      levDistance(t, tok) <= 1
    );
  }
  return false;
}

function scorePaper(p, query){
  if(!query) return 0;
  const q = query.toLowerCase();
  const terms = queryTerms(query);
  const fields = searchableFields(p);
  let score = 0;
  if(fields.title.includes(q)) score += 100;
  terms.forEach(t=>{
    if(termMatches(t, fields.title)) score += 50;
    if(termMatches(t, fields.authors)) score += 40;
    if(termMatches(t, fields.abstract)) score += 20;
    if(termMatches(t, fields.summary)) score += 5;
    if(termMatches(t, fields.tags)) score += 3;
  });
  return score;
}

function matchesSearch(p, query){
  if(!query) return true;
  const terms = queryTerms(query);
  const hay = searchHaystack(searchableFields(p));
  return terms.every(term => termMatches(term, hay));
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
  const layers = ['topic','method','task','modality','folder','arxiv','keyword'];

  layers.forEach(layer=>{
    const tags = byLayer[layer]||{};
    const entries = Object.entries(tags).sort((a,b)=>b[1]-a[1]);
    if(!entries.length) return;

    const section = document.createElement('div');
    section.className = 'layer-section' + (layer === 'topic' ? '' : ' collapsed');
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
  if(state.selectedTags.size) switchToTab('list');
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

// ── Virtual scroll ────────────────────────────────────────────────────────────
const VIRTUAL_SCROLL = {};
const VIRTUAL_EST_HEIGHT = 128;
const VIRTUAL_OVERSCAN = 8;

class VirtualScrollList {
  constructor(container, {estimatedHeight=VIRTUAL_EST_HEIGHT, overscan=VIRTUAL_OVERSCAN}={}){
    this.container = container;
    this.estimatedHeight = estimatedHeight;
    this.overscan = overscan;
    this.items = [];
    this.heights = [];
    this.offsets = [0];
    this.totalHeight = 0;
    this.renderItem = null;
    this._range = {start:-1, end:-1};
    this._scrollRaf = 0;
    this._measureRaf = 0;

    this.container.classList.add('virtual-scroll-host');
    this.spacer = document.createElement('div');
    this.spacer.className = 'virtual-scroll-spacer';
    this.viewport = document.createElement('div');
    this.viewport.className = 'virtual-scroll-viewport';
    this.container.innerHTML = '';
    this.container.appendChild(this.spacer);
    this.container.appendChild(this.viewport);

    this._onScroll = ()=>{
      if(this._scrollRaf) return;
      this._scrollRaf = requestAnimationFrame(()=>{ this._scrollRaf = 0; this._paint(); });
    };
    this.container.addEventListener('scroll', this._onScroll, {passive:true});
    this._ro = new ResizeObserver(()=>this._scheduleMeasure());
  }

  destroy(){
    this._ro.disconnect();
    if(this._scrollRaf) cancelAnimationFrame(this._scrollRaf);
    if(this._measureRaf) cancelAnimationFrame(this._measureRaf);
    this.container.removeEventListener('scroll', this._onScroll);
    this.container.classList.remove('virtual-scroll-host');
    delete VIRTUAL_SCROLL[this.container.id];
  }

  _scheduleMeasure(){
    if(this._measureRaf) return;
    this._measureRaf = requestAnimationFrame(()=>{ this._measureRaf = 0; this._measureVisible(); });
  }

  _measureVisible(){
    let changed = false;
    this.viewport.querySelectorAll('.virtual-scroll-row').forEach(row=>{
      const idx = +row.dataset.index;
      const h = row.offsetHeight;
      if(h > 0 && Math.abs((this.heights[idx]||0) - h) > 1){
        this.heights[idx] = h;
        changed = true;
      }
    });
    if(changed){
      this._rebuildOffsets();
      this.spacer.style.height = this.totalHeight + 'px';
      this._range = {start:-1, end:-1};
      this._paint();
    }
  }

  _rebuildOffsets(){
    this.offsets = [0];
    let sum = 0;
    for(let i = 0; i < this.items.length; i++){
      sum += this.heights[i] || this.estimatedHeight;
      this.offsets.push(sum);
    }
    this.totalHeight = sum;
  }

  _startIndex(scrollTop){
    let lo = 0, hi = this.items.length;
    while(lo < hi){
      const mid = (lo + hi) >> 1;
      if(this.offsets[mid + 1] <= scrollTop) lo = mid + 1;
      else hi = mid;
    }
    return lo;
  }

  _endIndex(scrollBottom){
    let lo = 0, hi = this.items.length;
    while(lo < hi){
      const mid = (lo + hi) >> 1;
      if(this.offsets[mid] < scrollBottom) lo = mid + 1;
      else hi = mid;
    }
    return lo;
  }

  _paint(){
    const n = this.items.length;
    if(!n || !this.renderItem) return;
    const scrollTop = this.container.scrollTop;
    const viewH = this.container.clientHeight || window.innerHeight;
    const start = Math.max(0, this._startIndex(scrollTop) - this.overscan);
    const end = Math.min(n, this._endIndex(scrollTop + viewH) + this.overscan);
    if(start === this._range.start && end === this._range.end) return;
    this._range = {start, end};

    this._ro.disconnect();
    const top = this.offsets[start];
    this.viewport.style.transform = `translateY(${top}px)`;
    const frag = document.createDocumentFragment();
    for(let i = start; i < end; i++){
      const row = document.createElement('div');
      row.className = 'virtual-scroll-row';
      row.dataset.index = i;
      row.innerHTML = this.renderItem(this.items[i], i);
      frag.appendChild(row);
      this._ro.observe(row);
    }
    this.viewport.replaceChildren(frag);
    this._scheduleMeasure();
  }

  setData(items, renderItem, {resetScroll=true}={}){
    this.items = items;
    this.renderItem = renderItem;
    this.heights = items.map(()=>this.estimatedHeight);
    this._rebuildOffsets();
    this.spacer.style.height = this.totalHeight + 'px';
    this._range = {start:-1, end:-1};
    if(resetScroll) this.container.scrollTop = 0;
    this._paint();
  }

  invalidate(){
    this._range = {start:-1, end:-1};
    this._paint();
  }
}

function getVirtualList(containerId, opts){
  const el = document.getElementById(containerId);
  if(!el) return null;
  if(VIRTUAL_SCROLL[containerId]) return VIRTUAL_SCROLL[containerId];
  VIRTUAL_SCROLL[containerId] = new VirtualScrollList(el, opts);
  return VIRTUAL_SCROLL[containerId];
}

function destroyVirtualList(containerId){
  VIRTUAL_SCROLL[containerId]?.destroy();
}

function renderVirtualList(containerId, items, renderItem, emptyHtml, opts={}){
  const el = document.getElementById(containerId);
  if(!el) return;
  if(!items.length){
    destroyVirtualList(containerId);
    el.innerHTML = emptyHtml;
    return;
  }
  const vl = getVirtualList(containerId, opts);
  vl.setData(items, renderItem, {resetScroll: opts.resetScroll !== false});
}

function refreshVirtualLists(){
  Object.values(VIRTUAL_SCROLL).forEach(vl=>vl.invalidate());
}

function renderPaperCard(p, highlight='', showReadDate=false){
  const tags = p.tags||{};
  const allTags = tags.all||[];
  const tagHtml = allTags.map(t=>{
    const layer = tagLayer(t,p);
    const cls = LAYER_COLORS[layer]||'topic';
    return `<span class="badge ${cls}" data-tag="${esc(t)}" title="${layer}">${esc(t)}</span>`;
  }).join('');
  const libCls = p.library==='auto_ai'?'lib-auto':'lib-phys';
  const yr = `${p.pub_year}${p.pub_month?'-'+String(p.pub_month).padStart(2,'0'):''}`;
  const src = (p.pub_date_source && p.pub_date_source !== 'arxiv_id') ? `<span class="source-tag" title="日期来源">${SOURCE_LABELS[p.pub_date_source]||p.pub_date_source}</span>` : '';
  const arxiv = p.arxiv_id ? `<a href="https://arxiv.org/abs/${p.arxiv_id}" target="_blank">arXiv</a>` : '';
  const altNote = (p.alternate_paths && p.alternate_paths.length)
    ? `<span class="alt-copies" title="${esc(p.alternate_paths.join('\\n'))}">另有 ${p.alternate_paths.length} 份副本</span>` : '';
  const readNote = (showReadDate && p.mtime)
    ? `<span class="read-tag" title="下载 ${fmtTs(p.birthtime)}">阅读 ${fmtTs(p.mtime)}</span>` : '';
  const title = highlightText(p.title||'', highlight);
  const authors = authorsText(p);
  const authorLine = authors
    ? `<div class="paper-meta" style="margin-top:-4px;margin-bottom:6px">${highlightText(authors, highlight)}</div>`
    : '';
  return `<div class="paper-card">
    <div class="paper-title">${title}</div>
    ${authorLine}
    ${p.summary_zh?`<div class="paper-summary">${esc(p.summary_zh)}</div>`:''}
    <div class="paper-meta">
      <span class="badge ${libCls}">${p.library}</span>
      <span>${esc(p.folder||'')}</span>
      <span>${yr}${src}</span>
      ${readNote}
      ${arxiv}
      ${altNote}
    </div>
    <div class="paper-tags">${tagHtml||'<span style="color:var(--muted);font-size:11px">无标签</span>'}</div>
  </div>`;
}

function renderPaperList(containerId, ps, showReadDate=false){
  const sorted = sortPapers(ps);
  renderVirtualList(
    containerId,
    sorted,
    p=>renderPaperCard(p, state.query, showReadDate),
    '<div class="empty-state"><div class="icon">🔍</div><div>没有匹配的论文</div></div>'
  );
}

// ── Unparsed list ─────────────────────────────────────────────────────────────
function unparsedListed(u){
  if(u.reason === 'duplicate' && state.unparsedReason !== 'duplicate') return false;
  return true;
}

function unparsedDefaultCount(){
  return UNPARSED.filter(u=>u.reason !== 'duplicate').length;
}

function updateUnparsedTabCount(){
  const el = document.getElementById('tab-unparsed-cnt');
  if(el) el.textContent = unparsedDefaultCount();
}

function filteredUnparsed(){
  let items = UNPARSED.filter(unparsedListed);
  if(state.library !== 'all') items = items.filter(u=>u.library === state.library);
  if(state.unparsedReason !== 'all') items = items.filter(u=>u.reason === state.unparsedReason);
  if(state.query){
    const hay = [
      u.filename, u.stem, u.title, u.rel_path, u.path, u.folder,
      unparsedReasonLabel(u.reason),
    ].filter(Boolean).join(' ').toLowerCase();
    items = items.filter(u=>matchesSearch({title:u.title, authors:'', abstract:hay}, state.query));
  }
  return items;
}

function renderUnparsedCard(u){
  const libCls = u.library === 'auto_ai' ? 'lib-auto' : 'lib-phys';
  const reasonCls = unparsedReasonClass(u.reason);
  const reasonLabel = unparsedReasonLabel(u.reason);
  const title = u.title
    ? highlightText(u.title, state.query)
    : `<span style="color:var(--muted)">（无标题）</span>`;
  const titleNote = u.title_from_filename ? ' · 来自文件名' : '';
  const arxiv = u.arxiv_id ? `<span>arXiv ${esc(u.arxiv_id)}</span>` : '';
  const mtime = u.mtime ? `<span title="修改时间">mtime ${fmtTs(u.mtime)}</span>` : '';
  const size = u.size != null ? `<span>${Math.round(u.size/1024)} KB</span>` : '';
  const junk = (u.junk_reasons && u.junk_reasons.length)
    ? `<span title="${esc(u.junk_reasons.join(', '))}">垃圾标题</span>` : '';
  const needsReview = u.needs_review ? '<span class="badge fail-warn">需复核</span>' : '';
  return `<div class="paper-card">
    <div class="unparsed-stem">${highlightText(u.filename || u.stem, state.query)}</div>
    <div class="paper-title">${title}${titleNote ? `<span style="font-size:11px;color:var(--muted);font-weight:400">${titleNote}</span>` : ''}</div>
    <div class="paper-meta">
      <span class="badge ${reasonCls}">${esc(reasonLabel)}</span>
      ${needsReview}
      <span class="badge ${libCls}">${esc(u.library||'')}</span>
      <span>${esc(u.folder||'')}</span>
      ${arxiv}
      ${mtime}
      ${size}
      ${junk}
    </div>
  </div>`;
}

function renderUnparsedList(){
  const items = filteredUnparsed();
  const visibleTotal = UNPARSED.filter(u=>{
    if(!unparsedListed(u)) return false;
    if(state.library !== 'all' && u.library !== state.library) return false;
    return true;
  }).length;
  const reasonCounts = {};
  UNPARSED.forEach(u=>{
    if(!unparsedListed(u)) return;
    if(state.library !== 'all' && u.library !== state.library) return;
    reasonCounts[u.reason] = (reasonCounts[u.reason]||0) + 1;
  });
  const reasonParts = Object.entries(reasonCounts)
    .sort((a,b)=>b[1]-a[1])
    .slice(0,4)
    .map(([r,c])=>`${unparsedReasonLabel(r)} ${c}`);
  updateUnparsedTabCount();
  let info = state.library === 'all'
    ? `未解析文件 · ${items.length} / ${visibleTotal} 个`
    : `未解析 · ${state.library} · ${items.length} 个`;
  if(reasonParts.length) info += ' · ' + reasonParts.join(' · ');
  if(state.query) info = `搜索「${state.query}」· ${items.length} 个`;
  if(state.unparsedReason !== 'all') info += ` · ${unparsedReasonLabel(state.unparsedReason)}`;
  document.getElementById('unparsed-info').textContent = info;

  const sorted = [...items].sort((a,b)=>{
    const ma = a.mtime||0, mb = b.mtime||0;
    if(mb !== ma) return mb - ma;
    return (a.stem||'').localeCompare(b.stem||'');
  });
  renderVirtualList(
    'unparsed-list',
    sorted,
    u=>renderUnparsedCard(u),
    '<div class="empty-state"><div class="icon">📄</div><div>没有匹配的未解析文件</div></div>',
    {estimatedHeight:140}
  );
}

function populateUnparsedReasonFilter(){
  const sel = document.getElementById('unparsed-reason-filter');
  const counts = {};
  UNPARSED.forEach(u=>{
    if(u.reason === 'duplicate') return;
    counts[u.reason] = (counts[u.reason]||0) + 1;
  });
  Object.entries(counts)
    .sort((a,b)=>b[1]-a[1])
    .forEach(([reason,cnt])=>{
      const o = document.createElement('option');
      o.value = reason;
      o.textContent = `${unparsedReasonLabel(reason)} (${cnt})`;
      sel.appendChild(o);
    });
  sel.addEventListener('change', e=>{
    state.unparsedReason = e.target.value;
    renderUnparsedList();
  });
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
      switchToTab('list');
    };
  });
  el.querySelectorAll('th[data-tag]').forEach(th=>{
    th.onclick = ()=>{ toggleTag(th.dataset.tag); };
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
      switchToTab('list');
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
  sel.addEventListener('change', e=>{
    state.year=e.target.value;
    refresh();
    if(state.year!=='all') switchToTab('list');
  });
}

// ── Recent reading ────────────────────────────────────────────────────────────
function renderRecentReading(){
  const month = recentReadingPapers(READ_WINDOW_SEC);
  document.getElementById('reading-info').textContent =
    state.library==='all'
      ? `最近 30 天阅读 · ${month.length} 篇`
      : `最近 30 天阅读 · ${state.library} · ${month.length} 篇`;

  renderVirtualList(
    'reading-list',
    month,
    p=>renderPaperCard(p, '', true),
    '<div class="empty-state"><div class="icon">📖</div><div>近 30 天无阅读记录</div><div style="font-size:12px;margin-top:8px;color:var(--muted)">在 PDF 阅读器中打开并保存后，编辑时间会更新</div></div>'
  );
}

// ── Refresh all views ─────────────────────────────────────────────────────────
function refresh(){
  const ps = filtered();
  const total = state.library==='all'
    ? PAPERS.length
    : PAPERS.filter(p=>p.library===state.library).length;
  document.getElementById('stat-total').textContent = total;
  const recentEl = document.getElementById('stat-recent-read');
  if(recentEl) recentEl.textContent = recentReadingPapers(READ_WINDOW_SEC).length;
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
  renderPaperList('chart-paper-list', ps);
  if(state.activeTab==='heatmap') renderHeatmap();
  if(state.activeTab==='timeline') renderTimeline();
  if(state.activeTab==='reading' && HAS_READING) renderRecentReading();
  if(state.activeTab==='unparsed') renderUnparsedList();
}

// ── Event wiring ──────────────────────────────────────────────────────────────
function switchToTab(name){
  const tab = document.querySelector(`[data-tab="${name}"]`);
  if(tab) tab.click();
}

let searchTimer;
document.getElementById('search').addEventListener('input', e=>{
  clearTimeout(searchTimer);
  searchTimer=setTimeout(()=>{state.query=e.target.value.trim();refresh();},200);
});
document.getElementById('lib-filter').addEventListener('change', e=>{
  state.library=e.target.value; buildTagSidebar(); refresh();
  if(state.activeTab==='reading' && HAS_READING) renderRecentReading();
  if(state.activeTab==='unparsed') renderUnparsedList();
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
    const name = tab.dataset.tab;
    state.activeTab = name;
    document.querySelectorAll('.tab').forEach(t=>t.classList.toggle('active',t===tab));
    document.querySelectorAll('.tab-content').forEach(c=>c.classList.remove('active'));
    document.getElementById('tab-'+name).classList.add('active');
    if(name==='reading' && HAS_READING) renderRecentReading();
    if(name==='unparsed') renderUnparsedList();
    requestAnimationFrame(()=>{
      refreshVirtualLists();
      if(name==='chart'){
        const ps = filtered();
        renderTagChart(ps);
        renderPaperList('chart-paper-list', ps);
      }
      if(name==='heatmap') renderHeatmap();
      if(name==='timeline') renderTimeline();
    });
  };
});

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('click', e=>{
  const badge = e.target.closest('.badge[data-tag]');
  if(badge && badge.dataset.tag){ toggleTag(badge.dataset.tag); }
});
buildTagSidebar();
populateYearFilter();
populateUnparsedReasonFilter();
initTheme();
if(!HAS_READING){
  document.getElementById('stat-recent-read')?.closest('span')?.remove();
  document.getElementById('tab-reading-btn')?.remove();
  document.getElementById('tab-reading')?.remove();
  state.activeTab = 'list';
  document.querySelector('[data-tab=list]')?.classList.add('active');
  document.getElementById('tab-list')?.classList.add('active');
} else {
  state.activeTab = 'reading';
}
refresh();
</script>
</body>
</html>"""
