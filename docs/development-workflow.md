# Development Workflow

## Overview

This project follows **trunk-based development** with pull requests. `main` is the single trunk branch and must always be deployable. Work happens on short-lived feature branches that are merged to main via fast-forward only, producing a strictly linear history with original SHAs preserved. Every commit that reaches `main` must belong to an approved PR with passing status checks. These guarantees are enforced through a combination of GitHub branch protection rules, a CI action that validates fast-forward eligibility, and a developer merge workflow that bypasses GitHub's merge buttons.

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

GitHub will reject the push unless the PR is approved, required checks passed, and history is linear.

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

## GitHub Repository Configuration

The following settings enforce fast-forward only, linear history, and PR-approved commits on `main`.

### Disable GitHub Merge Methods

**Settings → Pull Requests**

* ❌ Allow merge commits
* ❌ Allow squash merging
* ❌ Allow rebase merging

This forces all merges to happen outside the UI and prevents SHA rewriting.

NOTE: GitHub requires at least one method enabled. Select "Allow merge commits" and disable the other two. The branch protection rule "Require linear history" on `main` will block any attempted merge commit.

### Branch Protection Rules for `main`

**Settings → Branches → Branch protection rule (main)**

Enable:

* ✅ Require a pull request before merging
* ✅ Require approvals (≥1)
* ✅ Require status checks to pass
* ❌ Allow force pushes
* ❌ Allow bypass by admins (if you want strict enforcement)

This ensures no commit can reach `main` unless it belongs to an approved PR.

### FF-Only Enforcement via GitHub Action

A workflow fails the PR unless the branch is a direct descendant of `main`:

```yaml
name: Enforce FF-only
on: [pull_request]
jobs:
  ff:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout main branch
        uses: actions/checkout@v4
        with:
          ref: ${{ github.base_ref }}
          fetch-depth: 0
      - name: Fetch PR branch
        run: |
          git fetch origin ${{ github.head_ref }}:pr
      - name: Verify fast-forward is possible
        run: |
          git merge-base --is-ancestor HEAD pr
```

This check must be required in branch protection.

## Resulting Guarantees

| Trunk-Based Principle             | Status                         |
| --------------------------------- | ------------------------------ |
| Single trunk (`main`)             | ✅                              |
| Short-lived branches              | ✅ (rebase branch before merge) |
| Continuous integration            | ✅ (status checks required)     |
| Linear history                    | ✅ (FF-only)                    |
| No merge commits                  | ✅                              |
| PR-reviewed changes               | ✅                              |
| Only PR-approved commits to trunk | ✅                              |
| Original SHAs preserved           | ✅                              |

**Mental model:** GitHub enforces "approved commits only" via branch protection. The Action enforces "FF-only" via ancestry checks. Disabling merge buttons prevents SHA rewriting. Together, this is the only workflow that satisfies all three constraints simultaneously.
