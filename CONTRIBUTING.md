# Contributing to Call Analyzer

First off, thank you for considering contributing to Call Analyzer! It's people like you that make Call Analyzer such a great tool.

## 🚀 Getting Started

1. **Fork the repository** on GitHub.
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/call-analyzer.git
   cd call-analyzer
   ```
3. **Set up the development environment**. We use a Makefile to simplify this:
   ```bash
   make setup
   source venv/bin/activate
   ```
4. **Set your environment variables**:
   ```bash
   echo "API_KEY=your_gemini_api_key_here" > .env
   ```

## 🧪 Testing and Linting

Before pushing your changes, ensure they meet the project's quality standards.

To run the test suite:
```bash
make test
```

To run the linters (`flake8` and `mypy`):
```bash
make lint
```
*Note: All tests and linters **must pass** before a Pull Request can be accepted.*

## 🛠 Project Structure

- `src/` - The core application logic (Flask routes, AI models, PDF generation).
- `tests/` - The `pytest` suite testing all pipelines.
- `web/` - The frontend HTML/CSS/JS files (Glassmorphism layout).

## 📫 Pull Request Process

1. Create a feature branch: `git checkout -b feature/amazing-feature`
2. Make your incredible changes and commit consistently.
3. Keep your PRs well-scoped and accompanied by tests for new functionality.
4. Ensure the UI remains responsive and matches the Glassmorphism aesthetic.
5. Push to your branch and submit the PR!

## 📜 Code of Conduct

Please note that this project is released with a Contributor Code of Conduct. By participating in this project you agree to abide by its terms. Ensure interactions are respectful, welcoming, and constructive.
