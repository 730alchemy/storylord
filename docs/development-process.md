# Development Process

## Trunk-Based Development with PRs

| Trunk-Based Principle             | Your Workflow                  |
| --------------------------------- | ------------------------------ |
| Single trunk (`main`)             | ✅                              |
| Short-lived branches              | ✅ (rebase branch before merge) |
| Continuous integration            | ✅ (status checks required)     |
| Linear history                    | ✅ (FF-only)                    |
| No merge commits                  | ✅                              |
| PR-reviewed changes               | ✅                              |
| Only PR-approved commits to trunk | ✅                              |

To enforce **fast-forward only**, **linear history**, and **only PR-approved commits** into `main`, configure GitHub around **branch protection + FF validation**, and disallow GitHub’s merge buttons.

---

## 1. Disable GitHub merge methods (prevents SHA rewriting)

**Settings → Pull Requests**

* ❌ Allow merge commits
* ❌ Allow squash merging
* ❌ Allow rebase merging

This forces all merges to happen outside the UI.
NOTE: GitHub requires at least one. Select "Allow merge commits", disable the other other 2. Branch protection rule "Require linear history" on the main branch will block the attempted merge.

---

## 2. Protect `main` (enforces PR approval)

**Settings → Branches → Branch protection rule (main)**

Enable:

* ✅ Require a pull request before merging
* ✅ Require approvals (≥1)
* ✅ Require status checks to pass
* ❌ Allow force pushes
* ❌ Allow bypass by admins (if you want strict enforcement)

This ensures:

> No commit can reach `main` unless it belongs to an approved PR.

---

## 3. Enforce true fast-forward only with a GitHub Action

Add a workflow that fails unless the PR branch is a direct descendant of `main`:

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

Then require this check in branch protection.

This guarantees:

* PR branch is already rebased
* merge would be `git merge --ff-only`
* no merge commits possible

---

## 4. Required developer workflow

After PR approval:

```bash
git checkout main
git pull
git merge --ff-only feature-branch
git push origin main
```

GitHub will reject the push unless:

* the PR is approved
* required checks passed
* history is linear

---

## Resulting guarantees

You get all three:

* ✅ Fast-forward only (no merge commits)
* ✅ Linear history
* ✅ Only commits from approved PRs reach `main`
* ✅ Original SHAs preserved

---

## Mental model

GitHub enforces **“approved commits only”** via branch protection.
The Action enforces **“FF-only”** via ancestry checks.
Disabling merge buttons prevents SHA rewriting.

Together, this is the only workflow that satisfies all three constraints simultaneously.
