# GitHub Security & CI Quick Start Guide

## ✅ What's Already Done

This PR implements the following GitHub-native security and CI/CD features:

- ✅ **CI Tests Workflow** - Automated lint, type-check, unit/integration/security/property tests
- ✅ **CodeQL Security Analysis** - Automated security scanning for Python code
- ✅ **Dependabot Configuration** - Automated dependency updates for Python packages and GitHub Actions
- ✅ **PR Template** - Standardized template with security impact assessment
- ✅ **CODEOWNERS** - Automatic review requests for security-sensitive areas
- ✅ **Auto-Labeler** - Automatic PR labeling based on changed files
- ✅ **Documentation** - Comprehensive setup guide (see SECURITY_CI_SETUP.md)

## ⚠️ Action Required: Post-Merge Configuration

After merging this PR, repository administrators must configure these settings **manually in GitHub**:

### 1. Enable Secret Scanning (2 minutes)

**Why:** Prevents accidental commit of API keys, tokens, and passwords

**Steps:**
1. Go to **Settings** → **Code security and analysis**
2. Find "Secret scanning" section
3. Click **Enable** button
4. Enable **Push protection** (recommended) - blocks pushes containing secrets

### 2. Configure Branch Protection for `main` (5 minutes)

**Why:** Prevents direct pushes to main, requires PR reviews and passing CI checks

**Steps:**
1. Go to **Settings** → **Branches**
2. Click **Add rule** or edit existing rule for `main`
3. Enter branch name pattern: `main`

**Required settings:**

**A. Require pull request before merging:**
- ✅ Required approvals: **1** (minimum)
- ✅ Dismiss stale pull request approvals when new commits are pushed
- ✅ Require review from Code Owners

**B. Require status checks to pass before merging:**
- ✅ Require branches to be up to date before merging
- **Add required status checks** (type in search box and select):
  - `Lint (Ruff)`
  - `Type Check (Mypy)`
  - `Tests (Python 3.10)`
  - `Tests (Python 3.11)`
  - `Tests (Python 3.12)`
  - `Property-Based Tests`
  - `Analyze Python Code`
  - `All CI Checks Passed`

**C. Additional protections (recommended):**
- ✅ Require conversation resolution before merging
- ✅ Do not allow bypassing the above settings (applies to admins)

4. Click **Create** or **Save changes**

### 3. Verify Setup (2 minutes)

Create a test PR to verify:
- [ ] All CI checks run automatically
- [ ] Labels are applied automatically
- [ ] CODEOWNERS review requests work
- [ ] Branch protection prevents merge until checks pass

---

## 📋 Required Status Checks Reference

Copy-paste these exact names when adding required status checks to branch protection:

```
Lint (Ruff)
Type Check (Mypy)
Tests (Python 3.10)
Tests (Python 3.11)
Tests (Python 3.12)
Property-Based Tests
Analyze Python Code
All CI Checks Passed
```

---

## 🔒 Security Best Practices

### Secrets Management
- ❌ **Never** commit secrets, API keys, or passwords to the repository
- ✅ Use GitHub Actions Secrets: Settings → Secrets and variables → Actions
- ✅ Reference in workflows as `${{ secrets.SECRET_NAME }}`
- ✅ Use environment variables at runtime (see `env.example`)

### PR Security Requirements
Every PR must:
1. Pass all CI checks (lint, type-check, tests)
2. Pass CodeQL security analysis
3. Include security impact assessment in PR description
4. Have tests for new functionality
5. Document regression risk

---

## 📚 Documentation

For detailed information, see:
- **SECURITY_CI_SETUP.md** - Complete setup guide with all details
- **PR Template** - `.github/pull_request_template.md` - Security and testing requirements
- **CODEOWNERS** - `.github/CODEOWNERS` - Code ownership assignments

---

## 🆘 Troubleshooting

**Q: CI checks aren't running on PRs**
- A: Workflows may need one push to `main` to be activated. Merge this PR first.

**Q: Branch protection says "some checks haven't run yet"**
- A: The status check names must exactly match the job names in workflows. Wait for the first PR to see available check names.

**Q: Dependabot PRs are failing CI**
- A: Review the failure, merge security updates first, group non-security updates.

**Q: CodeQL analysis is taking too long**
- A: First run takes longer (15-20 min). Subsequent runs are faster (5-10 min).

**Q: How do I add a new secret?**
- A: Settings → Secrets and variables → Actions → New repository secret

---

## ✅ Success Criteria

You'll know the setup is complete when:
- ✅ Secret scanning is active (Settings shows "Enabled")
- ✅ Branch protection rule exists for `main` with all required checks
- ✅ Test PR demonstrates all checks running and labels applied
- ✅ Direct push to `main` is blocked
- ✅ Dependabot creates its first update PR

---

## 📊 Monitoring

### Weekly
- Review Dependabot PRs and merge approved updates
- Check Security → Code scanning alerts
- Review any secret scanning alerts

### Monthly
- Verify CI workflow performance
- Update CODEOWNERS if team structure changes
- Review branch protection rules

---

## 🎯 Expected Timeline

- **Post-merge setup:** 10-15 minutes (one-time)
- **First CodeQL run:** 15-20 minutes
- **First Dependabot PR:** Within 1 week (Monday 09:00 UTC)
- **Ongoing maintenance:** ~30 minutes/week

---

**Questions?** See SECURITY_CI_SETUP.md for detailed documentation or open an issue.
