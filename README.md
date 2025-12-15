# Trustworthy Model Registry — Phase 2 (Group 112)

This repository continues the Trustworthy Model Registry project for the **Software Engineering (ECE 30861 / CSCI 450)** course.  
It extends the Phase 1 command-line tool built by **Group 111** into a **serverless AWS-hosted system** with CI/CD and a web UI.

---

## Overview

The registry evaluates and hosts machine-learning models and datasets for **quality** and **trustworthiness** using defined metrics.

**Phase 2 goals**

- Transition from CLI to REST API + Web UI
- Implement baseline CRUD, ingest, and enumeration endpoints
- Automate testing and deployment using GitHub Actions
- Deploy a serverless backend on AWS
- **Attempt** the Performance Track for Deliverable 2

---

## Tech Stack

| Component                    | Purpose                             |
| ---------------------------- | ----------------------------------- |
| **AWS Lambda + API Gateway** | Serverless compute + REST endpoints |
| **AWS S3 + DynamoDB**        | Artifact and metadata storage       |
| **CloudWatch**               | Logging and observability           |
| **GitHub Actions**           | CI pipeline and build automation    |
| **pytest · mypy · black**    | Testing, type-checking, linting     |
| **VS Code + Bash**           | Development environment             |

---

## Team 112

| Member                     | Role                      | Focus                                                    |
| -------------------------- | ------------------------- | -------------------------------------------------------- |
| **Rosa Sierra Villanueva** | Project Manager · Backend | Backend implementation, testing, CI/CD, documentation    |
| **Ryan Blue**              | Backend & DevOps Engineer | Initial AWS setup, backend scaffolding, CI configuration |
| **Sarah Papabathini**      | UI Engineer               | Web UI implementation and accessibility compliance       |

---

## Continuous Integration

Pull requests to `main` trigger GitHub Actions checks:

1. **Black --check** for formatting
2. **Mypy** for static type checking (metrics CLI)
3. **Pytest** with coverage enforcement
4. CLI smoke test

CI checks must pass before merging. Due to time constraints near submission, some merges were completed with reduced peer review while still enforcing CI validation.

---

## Phase 2 Enhancements

- Migrated Phase 1 CLI into a serverless AWS backend
- Implemented baseline API endpoints required by the specification
- Added CI workflows and deployment automation via AWS SAM
- Added a Web UI with verified WCAG 2.1 AA accessibility compliance
- Attempted Performance Track (full benchmarking not completed)

---

## Developer Setup

For detailed local setup instructions (Python environment, scripts, and CI notes),  
see [`docs/SETUP.md`](https://github.com/rsierrav/Phase2_Group112/blob/main/docs/SETUP.md).

---

## License & Acknowledgment

Developed for educational use in Purdue University’s Software Engineering course.  
Based on Group 111’s Phase 1 implementation.
