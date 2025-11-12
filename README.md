# Trustworthy Model Registry — Phase 2 (Group 112)

This repository continues the Trustworthy Model Registry project for the **Software Engineering (ECE 30861 / CSCI 450)** course.  
It extends the Phase 1 command-line tool built by **Group 111** into a **serverless AWS-hosted system** with CI/CD, a web UI, and live performance metrics.

---

## Overview

The registry evaluates and hosts machine-learning models and datasets for **quality** and **trustworthiness** using defined metrics.

**Phase 2 goals**

- Transition from CLI → REST API + Dashboard
- Implement CRUD, Ingest, and Enumerate endpoints
- Display CloudWatch performance metrics (p50/p95/p99 latency)
- Automate tests + deployments through GitHub Actions
- Follow the **Performance Track** for Deliverable 2

---

## Tech Stack

| Component                    | Purpose                             |
| ---------------------------- | ----------------------------------- |
| **AWS Lambda + API Gateway** | Serverless compute + REST endpoints |
| **AWS S3 + DynamoDB**        | Artifact + metadata storage         |
| **CloudWatch + CloudTrail**  | Observability + logging             |
| **GitHub Actions**           | CI/CD pipeline                      |
| **pytest · mypy · black**    | Testing · type-checking · linting   |
| **VS Code + Bash**           | Development environment             |

---

## Team 112

| Member                     | Role                      | Focus                                                    |
| -------------------------- | ------------------------- | -------------------------------------------------------- |
| **Rosa Sierra Villanueva** | Project Manager · Tester  | Testing · Validation · Documentation · Team Coordination |
| **Ryan Blue**              | Backend & DevOps Engineer | AWS Lambda · API Gateway · DynamoDB · CI/CD Integration  |
| **Sarah Papabathini**      | UI Engineer               | Upload + Enumerate Dashboard · CloudWatch Metrics        |

---

## Continuous Integration

Every push or PR to `main` or `develop` triggers GitHub Actions:

1. **Black --check** → formatting
2. **Mypy** → type check
3. **Pytest** → unit + integration tests
4. **Coverage report** uploaded as artifact

Branch protection rules require passing CI and one Code Owner review before merging.

---

## Phase 2 Enhancements

- Converted CLI to serverless AWS architecture
- Added automated CI/CD pipeline
- Added Code Owners and PR templates
- Introduced structured JSON logging + CloudWatch metrics
- Targeted Performance Track (throughput + latency optimizations)

---

## Developer Setup

For detailed local setup instructions (Python venv, VS Code config, scripts, and CI notes),  
see [`docs/SETUP.md`](https://github.com/rsierrav/Phase2_Group112/blob/main/docs/SETUP.md).

---

## License & Acknowledgment

Developed for educational use in Purdue University’s Software Engineering course.  
Based on Group 111’s Phase 1 implementation by Erik Perez, Tristan Gooding, Heh Kle, and Justin Akridge.
