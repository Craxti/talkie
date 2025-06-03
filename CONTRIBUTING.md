# Contributing to Talkie

Thank you for your interest in contributing to Talkie! This document provides guidelines for submitting merge requests (pull requests) and becoming a contributor.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/craxtitalkie.git`
3. Create a new branch: `git checkout -b feature/your-feature-name`
4. Install development dependencies: `pip install -e ".[dev]"`

## Before Submitting a Merge Request

Please ensure your MR (merge request) meets these requirements:

- [ ] Code follows the project's style guide (PEP 8)
- [ ] All tests pass (`pytest`)
- [ ] New tests added for new features
- [ ] Documentation updated if needed
- [ ] Changelog updated (if applicable)
- [ ] Branch is up to date with main

## Merge Request Process

1. **Title Format**: Use a clear, descriptive title
   - Feature: Add new feature X
   - Fix: Resolve issue with Y
   - Docs: Update installation guide
   - Test: Add tests for feature Z

2. **Description Template**:
   ```markdown
   ## Description
   Brief description of the changes

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update

   ## How Has This Been Tested?
   Describe the tests you ran

   ## Checklist
   - [ ] My code follows the style guidelines
   - [ ] I have performed a self-review
   - [ ] I have added tests
   - [ ] I have updated the documentation
   ```

3. **Code Quality**:
   - Follow Python best practices
   - Use type hints
   - Add docstrings for new functions/classes
   - Keep functions focused and small
   - Use meaningful variable names

4. **Testing Requirements**:
   - Add unit tests for new features
   - Ensure all tests pass on all supported platforms
   - Include integration tests if needed
   - Test edge cases

5. **Documentation**:
   - Update README.md if needed
   - Add docstrings for public APIs
   - Update API documentation
   - Include examples for new features

## Code Review Process

1. Maintainers will review your code within 1-2 weeks
2. Address any requested changes
3. Once approved, your code will be merged

## Development Guidelines

### Code Style
- Use [Black](https://github.com/psf/black) for formatting
- Follow PEP 8 guidelines
- Use type hints (Python 3.8+)
- Add docstrings in Google style

### Testing
- Write unit tests using pytest
- Aim for high test coverage
- Test cross-platform compatibility
- Include both positive and negative test cases

### Commit Messages
- Use clear, descriptive commit messages
- Follow conventional commits format:
  ```
  feat: add new feature X
  fix: resolve bug in Y
  docs: update installation guide
  test: add tests for Z
  ```

## Getting Help

- Create an issue for bug reports
- Join our community discussions
- Tag maintainers for urgent issues

## License

By contributing to Talkie, you agree that your contributions will be licensed under the project's license.

Thank you for contributing to Talkie! 🚀 