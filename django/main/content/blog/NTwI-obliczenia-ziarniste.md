# Fuzzy Number Arithmetic

A "fuzzy granule distance" project from the *New Technologies in Computer Science* course.

## Project Description

The program implements arithmetic operations on fuzzy numbers represented as triangular membership functions.

Each fuzzy number is defined by three parameters:

- **x1** (left point) — lower bound of the membership function's support
- **m** (center) — value with maximum membership degree (equal to 1)
- **x2** (right point) — upper bound of the membership function's support

Supported operations:

- display a single fuzzy number
- multiply a fuzzy number by a real scalar
- raise a fuzzy number to a power
- add two fuzzy numbers
- subtract two fuzzy numbers
- multiply two fuzzy numbers

## Requirements

- Python 3.10+
- uv

## Installation & Usage

Install dependencies:
```bash
uv sync
```

### Display a single fuzzy number
```bash
uv run python app.py x1 m x2
```

Example:
```bash
uv run python app.py 2 3 4
```

### Scalar multiplication or exponentiation
```bash
uv run python app.py x1 m x2 operator value
```

Examples:
```bash
uv run python app.py 2 3 4 * 2
uv run python app.py 2 3 4 ^ 2
```

### Operations on two fuzzy numbers
```bash
uv run python app.py x1_A m_A x2_A operator x1_B m_B x2_B
```

Examples:
```bash
uv run python app.py 2 3 4 + 5 6 7
uv run python app.py 2 3 4 - 1 2 3
uv run python app.py 2 3 4 * 1 2 3
```

### Chained operations on multiple fuzzy numbers
```bash
uv run python app.py x1_A m_A x2_A operator1 x1_B m_B x2_B operator2 x1_C m_C x2_C ...
```

Example:
```bash
uv run python app.py 2 3 4 + 5 6 7 - 1 2 3
```

## Fuzzy Set Theory

A fuzzy set is a set in which every element belongs to the set with a membership degree in the range [0, 1]. This project uses a triangular membership function defined by the parameters `x1`, `m`, and `x2`.

## Author

Krystian Stasica

## License

This project is released under the MIT License. See the `LICENSE` file.
