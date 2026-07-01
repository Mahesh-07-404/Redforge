# Contributing to RedForge

We welcome contributions to RedForge! Follow these guidelines to submit pull requests.

---

## Code Quality Standards

Before committing your changes, make sure your code adheres to our quality specifications:

1. **Formatter**: Run Black to format code files:
   ```bash
   black src/ tests/
   ```
2. **Import Sorting**: Sort python imports using isort:
   ```bash
   isort src/ tests/
   ```
3. **Linter**: Verify coding guidelines using Ruff:
   ```bash
   ruff check src/
   ```
4. **Type Check**: Validate static types using mypy:
   ```bash
   mypy src/
   ```

---

## Running Tests

Verify your code changes do not introduce regressions by running the test suite:

```bash
# Run all unit and integration tests
pytest

# Generate a coverage report
pytest --cov=src/
```

---

## Pull Request Guidelines

1. Fork the repository and create your feature branch: `git checkout -b feature/awesome-feature`.
2. Add comprehensive tests for any new features or bug fixes.
3. Verify all tests pass cleanly.
4. Open a pull request targeting the `main` branch. Provide a detailed explanation of your changes.
