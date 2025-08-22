# GitHub Repository Setup Guide

This guide explains how to configure your GitHub repository to require tests to pass before allowing PR merges.

## Overview

The repository is configured with GitHub Actions workflows that automatically run tests and code quality checks on every push and pull request. To enforce that these checks must pass before merging, you need to set up branch protection rules.

## GitHub Actions Workflows

### 1. CI Workflow (`.github/workflows/ci.yml`)
- **Triggers**: Push to main/develop branches and all PRs
- **What it does**:
  - Runs tests on Python 3.9, 3.10, and 3.11
  - Performs code linting (Black, isort, flake8, mypy)
  - Generates test coverage reports
  - Uploads coverage to Codecov (optional)

### 2. Test Workflow (`.github/workflows/test.yml`)
- **Triggers**: Push to main/develop branches and all PRs
- **What it does**:
  - Runs tests on multiple Python versions
  - Generates coverage reports

### 3. Lint Workflow (`.github/workflows/lint.yml`)
- **Triggers**: Push to main/develop branches and all PRs
- **What it does**:
  - Code formatting checks (Black)
  - Import sorting (isort)
  - Style checking (flake8)
  - Type checking (mypy)

## Setting Up Branch Protection Rules

### Step 1: Access Repository Settings
1. Go to your GitHub repository
2. Click on **Settings** tab
3. In the left sidebar, click **Branches**

### Step 2: Add Branch Protection Rule
1. Click **Add rule** or **Add branch protection rule**
2. In **Branch name pattern**, enter:
   - `main` (for your main branch)
   - `develop` (if you use a develop branch)

### Step 3: Configure Protection Options
Enable these options:

#### Require status checks to pass before merging
- ✅ **Require status checks to pass before merging**
- ✅ **Require branches to be up to date before merging**
- In the search box, type and select:
  - `test` (from the CI workflow)
  - `lint` (from the lint workflow)

#### Additional Protection Options (Recommended)
- ✅ **Require pull request reviews before merging**
  - Set to **1** or more approving reviews
- ✅ **Dismiss stale PR approvals when new commits are pushed**
- ✅ **Require conversation resolution before merging**
- ✅ **Restrict pushes that create files that are larger than 100 MB**

### Step 4: Save the Rule
1. Click **Create** or **Save changes**
2. Repeat for other protected branches if needed

## What Happens Now

### For Contributors
1. **Fork the repository** or create a feature branch
2. **Make changes** and push to your branch
3. **Create a Pull Request**
4. **GitHub Actions automatically run**:
   - Tests on all Python versions
   - Linting and code quality checks
   - Coverage generation

### For Maintainers
1. **Review the PR** for code quality
2. **Check that all status checks pass**:
   - ✅ `test` (CI workflow)
   - ✅ `lint` (Lint workflow)
3. **Merge only when all checks pass**

## Local Development Setup

### Install Development Dependencies
```bash
pip install -r requirements-dev.txt
```

### Run Tests Locally
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_users.py

# Run with markers
pytest -m "not slow"
```

### Run Linting Locally
```bash
# Format code with Black
black app/ tests/

# Sort imports with isort
isort app/ tests/

# Check code style with flake8
flake8 app/ tests/

# Type checking with mypy
mypy app/
```

### Pre-commit Hook (Optional)
Install pre-commit to automatically run checks before commits:

```bash
pip install pre-commit
pre-commit install
```

## Troubleshooting

### Tests Failing
1. Check the GitHub Actions logs for specific error messages
2. Run tests locally: `pytest -v`
3. Ensure all dependencies are installed: `pip install -r requirements-dev.txt`

### Linting Issues
1. **Black formatting**: Run `black app/ tests/` to auto-format
2. **Import sorting**: Run `isort app/ tests/` to sort imports
3. **Style issues**: Fix flake8 warnings manually

### Coverage Issues
- Tests must maintain at least 70% coverage
- Add tests for new functionality
- Use `# pragma: no cover` for intentionally untested code

## Best Practices

1. **Always run tests locally** before pushing
2. **Keep PRs small** and focused
3. **Write tests for new features**
4. **Maintain good test coverage**
5. **Use meaningful commit messages**
6. **Review code thoroughly** before merging

## Advanced Configuration

### Custom Status Checks
You can add more status checks by:
1. Creating additional GitHub Actions workflows
2. Adding them to the branch protection rules
3. Ensuring they run on the same triggers

### Coverage Thresholds
The CI workflow requires 70% coverage. To change this:
1. Edit `.github/workflows/ci.yml`
2. Modify the `--cov-fail-under=70` parameter

### Matrix Testing
The workflow tests against multiple Python versions. To modify:
1. Edit `.github/workflows/ci.yml`
2. Update the `python-version` matrix
