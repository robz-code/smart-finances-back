#!/bin/bash

# Smart Finances - Local Development Checks
# This script runs all the same checks that GitHub Actions will run

set -e  # Exit on any error

echo "🚀 Running Smart Finances development checks..."
echo "================================================"

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: Virtual environment not detected"
    echo "   Consider activating your virtual environment first"
fi

echo ""
echo "📦 Installing/updating dependencies..."
pip install -r requirements-dev.txt

echo ""
echo "🔍 Running linting checks..."

echo "  • Black (code formatting)..."
black --check --diff app/ tests/ || {
    echo "❌ Black formatting check failed. Run 'black app/ tests/' to fix"
    exit 1
}

echo "  • isort (import sorting)..."
isort --check-only --diff app/ tests/ || {
    echo "❌ isort check failed. Run 'isort app/ tests/' to fix"
    exit 1
}

echo "  • flake8 (code style)..."
flake8 app/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics || {
    echo "❌ flake8 critical errors found"
    exit 1
}
flake8 app/ tests/ --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics

echo "  • mypy (type checking)..."
mypy app/ --ignore-missing-imports --no-strict-optional || {
    echo "❌ mypy type checking failed"
    exit 1
}

echo ""
echo "🧪 Running tests..."
pytest tests/ -v --cov=app --cov-report=term-missing --cov-fail-under=70 || {
    echo "❌ Tests failed or coverage below 70%"
    exit 1
}

echo ""
echo "✅ All checks passed! Your code is ready for GitHub."
echo "================================================"
echo "💡 Next steps:"
echo "   1. Commit your changes"
echo "   2. Push to your branch"
echo "   3. Create a Pull Request"
echo "   4. GitHub Actions will run these same checks automatically"
