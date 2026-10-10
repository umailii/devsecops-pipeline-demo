# DevSecOps Pipeline Demo

A GitHub Actions pipeline that runs security checks on every push, plus a small Flask API for it to scan. The point is to show the pipeline doing its job: one run that passes on clean code and one that fails on code with known problems.

## What the pipeline does

The workflow is [`.github/workflows/security.yml`](.github/workflows/security.yml). It runs on every push and pull request, with read-only repository permissions.

| Job | Tool | What it catches | Fails the build when |
|-----|------|-----------------|----------------------|
| Unit tests | pytest | Broken behavior, including a test that SQL input is not executed | any test fails |
| Secret scan | gitleaks | Credentials committed to the repo, across the full git history | a secret is found |
| Static analysis | Bandit | Risky code patterns such as `shell=True` and Flask `debug=True` | a HIGH severity issue is found |
| Dependency scan | pip-audit | Pinned packages with known vulnerabilities | any known vulnerability is found |
| Container scan | Trivy | Dockerfile misconfigurations, and OS and library vulnerabilities in the built image | a HIGH or CRITICAL issue is found (image scan ignores issues with no fix yet) |

Dependabot also opens weekly update pull requests for the Python packages, the GitHub Actions and the Docker base image.

## The sample app

[`app/main.py`](app/main.py) is a tiny notes API:

- `POST /notes` creates a note
- `GET /notes?q=term` searches note titles
- `GET /resolve?host=example.com` looks up a hostname
- `GET /health` returns `ok`

The code on `main` is the clean version. It uses parameterized SQL, validates the hostname before using it, binds to localhost, reads settings from the environment, and runs in a container as a non-root user.

## The failing run

The `main` branch is the passing version. To produce the failing run, create a branch from it and apply [`make-vulnerable.patch`](make-vulnerable.patch) (kept alongside the repo, not inside it):

```bash
git checkout -b demo/vulnerable
git apply make-vulnerable.patch
git add -A
git commit -m "Demo: reintroduce vulnerable code"
git push -u origin demo/vulnerable
```

The patch puts back the kinds of problems the pipeline exists to catch:

| Change | Caught by |
|--------|-----------|
| AWS-style access key and secret written into `app/config.py` (random fake values, not real credentials) | gitleaks |
| `subprocess.check_output(..., shell=True)` built from user input, and `debug=True` | Bandit |
| Old pinned Flask and Werkzeug versions with known CVEs | pip-audit |
| SQL built with an f-string | the unit test |
| Dockerfile runs as root (no non-root `USER`), plus an old `python:3.8.0` base image | Trivy (the run flagged the root user, DS-0002) |

Because the fake key is committed on that branch, it stays in that branch's history. That is why the failing branch is created from `main` and never merged back.

## Local results

I ran the checks locally against both versions before publishing:

| Check | `main` (clean) | `demo/vulnerable` |
|-------|----------------|-------------------|
| pytest | 5 passed | 2 failed (SQL injection test, shell metacharacter test) |
| Bandit, HIGH only | no issues | 2 issues (B602 `shell=True`, B201 `debug=True`) |
| pip-audit | no known vulnerabilities | 37 known vulnerabilities in 4 packages |
| gitleaks | no leaks | 2 leaks found |

The Trivy container jobs ran on GitHub, and the results are in the linked runs below.

## Real runs on GitHub


- Passing run on `main`: [Security pipeline #16](https://github.com/umailii/devsecops-pipeline-demo/actions/runs/38082921683)
- Failing run on `demo/vulnerable`: [Security pipeline #17](https://github.com/umailii/devsecops-pipeline-demo/actions/runs/38083048747)

## Running it locally

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest
python -m app.main
```

To run the same scans the pipeline runs:

```bash
pip install bandit pip-audit
bandit -r app -lll
pip-audit -r requirements.txt
```

## Limits

This is a demonstration pipeline, not a complete security program. The scanners only find known patterns and known vulnerabilities, so a passing run does not mean the app is secure. The sample app is small on purpose and is not meant to be deployed.
