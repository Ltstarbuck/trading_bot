# Contributing to Trading Bot

First off, thank you for considering contributing to Trading Bot! It's people like you that make Trading Bot such a great tool.

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* Use a clear and descriptive title
* Describe the exact steps which reproduce the problem
* Provide specific examples to demonstrate the steps
* Describe the behavior you observed after following the steps
* Explain which behavior you expected to see instead and why
* Include screenshots if possible

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* Use a clear and descriptive title
* Provide a step-by-step description of the suggested enhancement
* Provide specific examples to demonstrate the steps
* Describe the current behavior and explain which behavior you expected to see instead
* Explain why this enhancement would be useful

### Pull Requests

* Fill in the required template
* Do not include issue numbers in the PR title
* Include screenshots and animated GIFs in your pull request whenever possible
* Follow the Python style guide
* Include tests for new features
* Document new code based on the Documentation Styleguide

## Development Process

1. Fork the repo
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run the tests (`pytest`)
5. Commit your changes (`git commit -m 'Add some amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Development Setup

1. Install Python 3.9 or later
2. Clone the repository
3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```
5. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Testing

* Run all tests: `pytest`
* Run specific test file: `pytest tests/test_file.py`
* Run with coverage: `pytest --cov=app`

## Style Guide

* Follow PEP 8
* Use type hints
* Write docstrings for all public methods
* Keep functions focused and small
* Use meaningful variable names

## Documentation

* Use Google style docstrings
* Update the README.md with details of changes to the interface
* Update the CHANGELOG.md following semantic versioning

## Questions?

Feel free to open an issue with your question or contact the maintainers directly.
