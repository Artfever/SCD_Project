# Contributing

## First time

1. Accept the repository invitation and clone it.
2. Set your own identity: `git config user.name "..."` and `git config user.email "..."` (use an
   email linked to your GitHub account so commits count as yours).
3. Enable the commit check: `git config core.hooksPath .githooks`.
4. Follow the setup steps in the README and run `bash scripts/check.sh`.

## One task, one issue, one pull request

```bash
git switch main && git pull
git switch -c feat/7-verdict-gates          # type/issue-short-name
# work, then
git commit -m "feat(verdict): add hard gates"
git push -u origin HEAD
gh pr create --fill                          # put "Closes #7" in the description
```

- Conventional commits: `feat`, `fix`, `test`, `docs`, `chore`, `ci`, `build`, `refactor`, `perf`,
  `style`, `revert`, with an optional scope. The pull request title follows the same rule because it
  becomes the commit on `main`.
- Keep pull requests small and single-purpose.
- The other member reviews. Ask questions until you could explain the change yourself.
- After approval and green checks, the author squash-merges. The branch is deleted automatically.
- If `main` moved, update your branch before merging.

## Rules

- No direct pushes to `main`.
- Never commit secrets, `.env`, kubeconfigs, model weights or the course PDFs.
- Commits carry only the human author. No AI co-author lines or "generated with" footers.
- Record AI help honestly in [docs/ai-usage-log.md](docs/ai-usage-log.md): the course requires it,
  and you are responsible for every line.
- Collect data only through official APIs or permitted pages.
- A new design choice gets a record in [docs/decisions/](docs/decisions/).
