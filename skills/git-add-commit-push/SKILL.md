---
name: git-add-commit-push
description: >-
  Analyzes changed repos in the workspace, stages relevant files, writes a
  descriptive commit message, and pushes to the remote branch. Use when the
  user asks to git add/commit/push, "提交推送", "push", or `/git-add-commit-push`
  in the context of publishing work to a remote.
---

# Git add + commit + push

## When to apply

- User explicitly wants changes staged, committed, **and pushed** (including shorthand `/git-add-commit-push` or "提交推送").
- Prefer **executing** commands in the real repo(s), not only suggesting them.

## Workflow

1. **Locate repos**
   - List workspace directories; run `git status -sb` in each candidate root.
   - Identify every repo that has staged or unstaged changes.
   - Do not assume a single repo unless only one dirty tree is found.

2. **Inspect before staging**
   - Run `git diff --stat` (and `git diff --cached --stat` if partially staged).
   - Run `git log -3 --oneline` to match the project's commit-message style.
   - If the diff mixes unrelated concerns, suggest splitting commits; proceed with one commit only when the user confirms.

3. **Stage**
   - `git add` only paths that belong to the requested change.
   - Avoid `git add -A` unless the user asked to commit everything or the change set is clearly a single unit.
   - Skip secrets (`.env`, credentials, private keys) and large generated binaries — warn the user and exclude them unless explicitly overridden.

4. **Commit message**
   - Use imperative mood with a conventional-commit prefix: `fix:`, `feat:`, `refactor:`, `docs:`, `chore:`, etc.
   - Optional body: motivation or non-obvious behavior (complete sentences).
   - Match the style from `git log -3 --oneline`.
   - Pass the message via a HEREDOC to preserve formatting:
     ```bash
     git commit -m "$(cat <<'EOF'
     type(scope): short subject

     Optional longer body.
     EOF
     )"
     ```

5. **Push**
   - Determine the tracking branch: `git rev-parse --abbrev-ref --symbolic-full-name @{u}` (may be unset on new branches).
   - If a tracking branch exists: `git push`.
   - If no upstream is set: `git push -u origin HEAD` to publish the branch and set tracking.
   - **Never force-push** (`--force` / `--force-with-lease`) unless the user explicitly requests it; warn if main/master is the target.

6. **Verify**
   - Run `git status` to confirm the working tree is clean.
   - Run `git log -1 --oneline` to confirm the commit was pushed.

## Multi-repo note

When changes span multiple repos, repeat steps 2–6 in **each repo separately**, with commit messages appropriate to that repo's changes.

## Do not

- Amend or force-push without explicit user request.
- Push to `main`/`master` without warning the user.
- Commit secrets, `.env`, or large generated binaries.
