#!/bin/bash

echo "🔧 Setting up pre-commit and pre-push hooks..."

# Install pre-commit
echo "📦 Installing pre-commit framework..."
pip install pre-commit

# Install pre-commit hooks
echo "🪝 Installing pre-commit hooks..."
pre-commit install
pre-commit install --hook-type pre-push

# Make pre-push hook executable
chmod +x .git/hooks/pre-push

echo "✅ Hooks installed successfully!"
echo ""
echo "📋 Installed hooks:"
echo "   • pre-commit: Runs on 'git commit'"
echo "     - Black (code formatting)"
echo "     - isort (import sorting)"
echo "     - flake8 (linting)"
echo "     - pytest (unit tests + coverage ≥85%)"
echo "   • pre-push: Runs on 'git push'"
echo "     - Full test suite with coverage check"
echo "     - Backend linting"
echo ""
echo "ℹ️  To skip hooks temporarily: git commit --no-verify"
echo "ℹ️  To run hooks manually: pre-commit run --all-files"
