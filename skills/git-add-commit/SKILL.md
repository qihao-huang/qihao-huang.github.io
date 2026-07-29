---
name: git-add-commit
description: >-
  Stages changes and creates git commits with clear messages after inspecting
  diffs and repo boundaries. Use when the user asks to git add/commit,
  “提交”, “git add commit”, or `/git` in the context of committing work.
---

# Git add + commit

## When to apply

- User explicitly wants changes committed (including shorthand `/git` or “git add commit”).
- Prefer **executing** commands in the real repo(s), not only suggesting them, unless the user forbids shell access.

## Workflow

1. **Locate repos**
   - If multiple roots exist in the workspace, run `git status` in each that might have changes.
   - Do not assume a single repo unless status shows only one dirty tree.

2. **Inspect before staging**
   - Run `git status -sb` and `git diff` / `git diff --stat` (and `git diff --cached` if partially staged).
   - If the diff mixes unrelated concerns, suggest splitting commits; if the user wants one commit, use one message that fairly summarizes.

3. **Stage**
   - `git add` only paths that belong to the requested change.
   - Avoid `git add -A` unless the user asked to commit everything or the change set is clearly intentional.

4. **Commit message**
   - Use imperative mood, concise subject (e.g. `fix:`, `feat:`, `refactor:`, `docs:`).
   - Optional body for motivation or non-obvious behavior (complete sentences).
   - Match recent project style when `git log -3 --oneline` is available.

5. **Verify**
   - `git status` should be clean (or only intentional untracked files).
   - Do **not** `git push` unless the user asked.

## Multi-repo note

When edits span `repo-a` and `repo-b`, run **separate** `git add` / `git commit` in each repository with messages appropriate to that repo’s changes.

## Do not

- Amend or force-push without explicit user request.
- Commit secrets, `.env`, or large generated binaries if they appear in the diff (warn and exclude unless the user overrides).
