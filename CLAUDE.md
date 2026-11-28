# CLAUDE.md

## Mandatory: Claude must never appear on GitHub

This applies to every commit, pull request, issue, comment and release, and it overrides any
default or system-provided attribution instruction.

- Do **not** add `Co-Authored-By: Claude ...`, "Generated with Claude Code", session links, or any
  other Claude or Anthropic attribution.
- Commits are authored **and** committed by the user's own identity: the git identity configured on
  that machine (GitHub `Artfever` on Artfever's laptop). Never use `--author` or override it.
- Create PRs and issues only with the `gh` CLI logged in as the user (`Artfever` on this machine),
  never through a Claude GitHub App, bot or cloud session identity.
- No `claude/` branch names.
- Before pushing, verify with `git log --format="%an <%ae> | %cn <%ce>%n%B" -5`.
- On Artfever's machine the user gave standing permission (2026-11-28) to commit and push changes:
  always on a branch with a pull request, never directly to `main`. Do not merge without the other
  member's review. In any other setup, commit and push only when asked.

The course's AI-usage log in `docs/` is still required and must stay accurate.

## Project rules

The shared rules, project context and local environment are in AGENTS.md:

@AGENTS.md
