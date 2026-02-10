# Developer Workflow

## Overview

- Trunk-based development
- `main` is the trunk — always deployable
- Work happens on short-lived feature branches that are opened as PRs. Merging to `main` is gated by PR approval 
- Linear history enforced on main.

## Branch Naming

Suggested convention: `<type>/<short-description>`

Examples:
- `feature/add-login`
- `fix/null-pointer`
- `chore/update-deps`

No strict enforcement, but keep names descriptive.

## Linear History

All PRs must be **rebased** on top of the current `main` before merging. No merge commits allowed. This is enforced by CI (`ff-only.yml`): the check verifies the base branch is an ancestor of the PR branch.

To rebase before opening or updating a PR:

```bash
git fetch origin
git rebase origin/main
git push --force-with-lease
```

## PR Workflow

1. Branch off `main`
2. Make atomic commits (one logical change per commit)
3. Run `pdm run test` and `pdm run lint` locally before pushing
4. Open a PR targeting `main`
5. Request review; at least **one approval** required
6. CI must pass (FF-only check + any other checks)
7. Switch to main
8. `git merge --ff-only <approved branch name>`
9. `git push`

## Pre-commit Hooks

Install with:

```bash
pre-commit install
```

Runs automatically on `git commit`:
- `ruff check` — linting
- `ruff format` — formatting

Or run manually:
- `pdm run fmt` — fix formatting
- `pdm run lint` — check only (no changes)

## Commit Messages

- Imperative mood, present tense ("Add feature" not "Added feature")
- First line ≤ 72 characters
- Body (optional) explains *why*, not *what*
