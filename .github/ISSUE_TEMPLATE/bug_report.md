---
name: Bug report
about: Create a report to help us improve
title: '[BUG] '
labels: 'bug'
assignees: ''

---

## Bug Description
A clear and concise description of what the bug is.

## Steps to Reproduce
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## Expected Behavior
A clear and concise description of what you expected to happen.

## Actual Behavior
A clear and concise description of what actually happened.

## Screenshots
If applicable, add screenshots to help explain your problem.

## Environment
- **OS**: [e.g. macOS, Windows, Linux]
- **Python Version**: [e.g. 3.9, 3.10, 3.11]
- **App Version**: [e.g. 1.0.0]

## Additional Context
Add any other context about the problem here.

---

## Development Requirements

**If you're submitting a PR to fix this bug, please ensure:**

- [ ] **Tests are written** to reproduce the bug
- [ ] **Tests pass locally** (run `./scripts/run-checks.sh`)
- [ ] **Code follows style guidelines** (Black, isort, flake8, mypy)
- [ ] **Test coverage is maintained** (minimum 70%)
- [ ] **Bug is verified as fixed** with the new tests

**Note:** GitHub Actions will automatically run these checks on your PR. All checks must pass before the PR can be merged.
