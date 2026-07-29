---
name: save-answer-to-docs
description: >-
  Saves valuable structural chat answers into the workspace docs/ as durable
  markdown notes, updates the docs index, and avoids duplicating existing
  tutorials. Use when the user asks to 保存回答到 docs, 整理到 docs, save answer
  to docs, /save-docs, or to archive a reusable explanation into local notes.
---

# 保存回答到 docs

把对话里**可复用的结构性结论**落盘到工作区 `docs/`，而不是只留在聊天记录里。

## When to apply

- 用户明确说：保存回答到 docs / 整理到 docs / save answer to docs / `/save-docs`
- 用户要求把「上述回答 / 刚才的调研 / FAQ」写成本地笔记

## Defaults（Foundation）

| Item | Path |
|------|------|
| Docs root | `<workspace>/docs/`（本机常为 `/home/sany/Documents/Foundation/docs`） |
| Index | `docs/README.md`（无则创建简短索引表） |
| Language | **简体中文** |
| Commit | **默认不 commit / 不 push**（除非用户另说） |

若当前工作区没有 `docs/`，先问用户目标目录；不要写到无关仓库。

## Workflow

复制并跟踪：

```
Save → docs:
- [ ] 1. 判定要保存的内容范围（哪段回答 / 哪次调研）
- [ ] 2. 扫 docs/ 与 README，决定新建 vs 合并进已有笔记
- [ ] 3. 只提炼结构性结论（表格 + 可复制命令 + 坑）
- [ ] 4. 写入/更新 markdown
- [ ] 5. 更新 docs/README.md 索引一行
- [ ] 6. 向用户回报：路径 + 一句话用途（不 commit）
```

### 1. 选定内容

- 默认 = **最近一次**用户指称的回答（「上述 / 刚才 / 这个调研」）。
- 若范围不清：先列 2–4 个候选标题让用户确认，或按「最新一条完整调研」落盘。
- **不要**整段粘贴聊天流水账、工具日志、agent 元数据。

### 2. 新建还是合并

| 情况 | 做法 |
|------|------|
| 已有同主题笔记（如 `lerobot_wam_handson.md`） | **合并/补丁**：补缺、改错、加交叉链接；避免第二份平行长文 |
| 新主题 | `docs/<topic>_handson.md` 或 `docs/<topic>_notes.md`（小写+下划线） |
| 清单类（canvas、路径、下载状态） | 短文即可，如 `local_canvases_inventory.md` |

命名参考现有：`lerobot_*_*.md`、`local_*_inventory.md`。

### 3. 正文结构（模板）

```markdown
# <清晰标题>

> 一句话用途；链到相关 fullstack / FAQ / 矩阵（若有）

## 结论先看
| 问题 | 答案 |
|------|------|

## 可复制命令
（bash 块；本地实验默认 `push_to_hub=false`）

## 对照 / 坑
（表格；写清显存、Hub id、env 限制）

## 相关路径
```

文风：简洁、**表格优先**、命令可复制；标明核实日期或「对话整理」来源即可。

### 4. 更新索引

在 `docs/README.md` 的表格中增加或修正一行：`[文件名](./文件名) | 一句话用途`。  
若 README 不存在，创建含标题 + 表格的最小索引。

### 5. 回报用户

只报：

1. 新建/更新了哪些路径  
2. 各文件一句话用途  
3. 未 commit（除非用户要求提交）

## Do not

- 不要把 secrets、token、`.env` 写入 docs。
- 不要无请求地 `git commit` / `git push`。
- 不要复制整份官方文档；链到 `main/lerobot/docs/source/*.mdx` 即可。
- 不要为同一主题再开第三份重复笔记；先搜 `docs/`。
- 不要把 canvas 源码塞进 docs；清单用路径表，发布走 `canvas-to-github-io`。

## Examples

**Example A — 用户：「把上面 WAM 调研保存到 docs」**

1. 检查是否已有 `lerobot_wam_handson.md` → 有则补丁，无则新建。  
2. 更新 `README.md` 索引。  
3. 回报路径。

**Example B — 用户：「/save-docs 保存 canvas 列表」**

1. 枚举本机 `.canvas.tsx` 与 github.io catalog。  
2. 写入 `docs/local_canvases_inventory.md`（或更新已有清单）。  
3. 更新索引。
