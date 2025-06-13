# Test Suite Organization

This directory contains a well-organized test suite following Clean Architecture principles.

## Structure

```
tests/
├── unit/                           # Fast unit tests with mocking
│   ├── test_entities_and_use_cases.py    # Core business logic tests
│   └── usecases/                        # Use case specific unit tests
├── integration/                    # Integration tests with real dependencies
│   └── test_table_extraction.py          # End-to-end table extraction tests
├── samples/                        # Sample files for testing
├── README.md
└── __init__.py
```

## Running Tests

```bash
# Run fast unit tests
python -m unittest discover -s tests/unit

# Run full integration tests (requires models)
python -m unittest discover -s tests/integration

# Run all tests
python -m unittest discover -s tests
```

## Test Principles

1. **Unit tests** should be fast and use mocking for external dependencies
2. **Integration tests** can use real models but should be clearly marked
4. Each layer should be testable in isolation
