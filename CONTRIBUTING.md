# Contributing to FinMind AI

Thank you for your interest in contributing to FinMind AI! This document provides guidelines and information for contributors.

## How to Contribute

### 1. Fork the Repository
1. Fork the FinMind AI repository
2. Clone your fork locally
3. Create a new branch for your feature

### 2. Set Up Development Environment
```bash
# Clone your fork
git clone https://github.com/yigenfeng0707-netizen/finmind-ai.git
cd finmind-ai

# Install dependencies
cd backend
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Start development server
python -m uvicorn main:app --reload
```

### 3. Make Changes
1. Create a feature branch: `git checkout -b feature/amazing-feature`
2. Make your changes
3. Test your changes
4. Commit your changes: `git commit -m 'Add amazing feature'`
5. Push to the branch: `git push origin feature/amazing-feature`
6. Open a Pull Request

### 4. Code Style Guidelines
- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to all public functions
- Keep functions focused and concise
- Use type hints where appropriate

### 5. Testing
- Write tests for new features
- Ensure all existing tests pass
- Run the test suite before submitting:
```bash
python test_modules.py
```

### 6. Documentation
- Update README.md if adding new features
- Add API documentation for new endpoints
- Update CHANGELOG.md with your changes

## Development Rules

### Commit Messages
- Use conventional commits format
- Examples:
  - `feat: Add new analysis feature`
  - `fix: Resolve API timeout issue`
  - `docs: Update API documentation`
  - `test: Add unit tests for agent module`

### Pull Requests
- Provide a clear description of changes
- Reference any related issues
- Ensure CI/CD passes
- Request review from maintainers

### Code Review
- All PRs require at least one review
- Address feedback promptly
- Keep discussions constructive

## Getting Help

- Open an issue for bugs or feature requests
- Join our community discussions
- Check existing documentation

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Code of Conduct

Please follow our Code of Conduct in all interactions with the project.

Thank you for contributing to FinMind AI! 🚀
