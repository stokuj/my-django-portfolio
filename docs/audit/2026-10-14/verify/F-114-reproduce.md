# F-114: Python version prerequisite too loose (reproduce)

**Verdict:** CONFIRMED
**Confidence:** high
**Adjusted severity:** low (docs)

## Reasoning
- `README.md:106` says `- Python 3.13+`.
- `pyproject.toml:5` pins `requires-python = ">=3.13,<3.14"`, so 3.14 or later is rejected (uv refuses to resolve or sync).
- Other docs already agree with the pin: `README.md:49` says "Python 3.13", and CI uses `python-version: [3.13]` (`.github/workflows/django.yml:15`).
- So line 106 is the one place that says otherwise. A reader on Python 3.14 who follows it hits a resolver error.

## Proposal
Change `README.md:106` to `- Python 3.13`, which matches line 49. No better alternative.
