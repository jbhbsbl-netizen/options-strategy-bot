# CI/CD Setup Documentation

## Overview

This project now includes a complete **CI/CD pipeline** using GitHub Actions. Every time you push code to GitHub, it automatically:
- ✅ Runs all tests
- ✅ Checks code quality
- ✅ Verifies deployability

---

## What We Set Up

### 1. **GitHub Actions Workflow**
File: `.github/workflows/ci.yml`

**Triggers on:**
- Push to `main`, `master`, or `develop` branches
- Pull requests to these branches

**What it does:**
1. **Testing (test job)**
   - Runs on Python 3.9, 3.10, and 3.11
   - Installs all dependencies
   - Runs pytest tests
   - Generates coverage reports
   - Uploads to codecov.io

2. **Linting (lint job)**
   - Checks code formatting with `black`
   - Checks import sorting with `isort`
   - Lints code with `flake8`

3. **Deploy Check (deploy-check job)**
   - Verifies app can be imported
   - Checks main app file exists
   - Confirms deployment readiness

### 2. **Test Suite**
File: `tests/test_basic.py`

**Tests:**
- ✅ Core module imports
- ✅ YFinance client functionality
- ✅ Thesis data model
- ✅ Required packages installation

### 3. **Configuration Files**
- `pytest.ini` - Pytest configuration
- `requirements-dev.txt` - Development dependencies

---

## How to Use

### Local Testing (Before Push)
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term

# Check code formatting
black --check src/ tests/
```

### Push to GitHub
```bash
# Make your changes
git add .
git commit -m "Your commit message"
git push

# GitHub Actions automatically runs!
# Check: https://github.com/YOUR_USERNAME/YOUR_REPO/actions
```

### View CI/CD Results
1. Go to your GitHub repository
2. Click on **"Actions"** tab
3. See all workflow runs
4. Green checkmark = tests passed ✅
5. Red X = tests failed ❌

---

## Deployment to Streamlit Cloud

Once tests pass, you can deploy:

### Option 1: Streamlit Cloud (Recommended)
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Select your GitHub repository
4. Choose `app_professional.py` as the main file
5. Click "Deploy"

Your app will be live at: `https://YOUR_APP_NAME.streamlit.app`

### Option 2: Other Platforms
- **Heroku**: Add `Procfile` and deploy
- **Railway**: Connect repo and deploy
- **AWS/Azure**: Use container deployment

---

## GitHub Secrets (For Production)

If deploying, add these secrets to GitHub:

1. Go to your repo on GitHub
2. Settings → Secrets and variables → Actions
3. Add New Repository Secret:
   - `OPENAI_API_KEY` - Your OpenAI API key
   - `ANTHROPIC_API_KEY` - Your Anthropic API key

These are used in production deployment, not in tests.

---

## CI/CD Status Badge

Add this to your README.md to show build status:

```markdown
[![CI/CD Pipeline](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci.yml)
```

---

## Troubleshooting

### Tests Fail on GitHub but Pass Locally
- Check Python version (GitHub uses 3.9, 3.10, 3.11)
- Check dependencies in `requirements.txt`
- Check environment variables

### Deploy Check Fails
- Verify `app_professional.py` exists
- Check all imports work
- Test: `python -c "import streamlit; print('OK')"`

### Linting Warnings
- Run `black src/ tests/` to auto-format
- Run `isort src/ tests/` to sort imports
- These don't fail the build, just warn

---

## What Your Professor Will See

When you push code:
1. ✅ **Automated testing** on multiple Python versions
2. ✅ **Code quality checks** (linting, formatting)
3. ✅ **Deployment verification**
4. ✅ **Coverage reports** (optional)
5. ✅ **Professional CI/CD pipeline** using industry-standard tools

This demonstrates:
- Modern software engineering practices
- Automated quality assurance
- Deployment readiness
- Professional project structure

---

## Next Steps

1. **Push to GitHub** (see below)
2. **Verify workflows run** (check Actions tab)
3. **Add more tests** as you add features
4. **Deploy to Streamlit Cloud** when ready

---

## Initial GitHub Setup

If this is your first time pushing:

```bash
# Create repo on GitHub first, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git add .
git commit -m "Initial commit with CI/CD pipeline"
git push -u origin main
```

Your CI/CD pipeline will automatically run! 🚀

---

**✅ CI/CD Setup Complete!**

Every push now triggers automated testing and quality checks.
