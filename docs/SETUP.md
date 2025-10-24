# Setup Guide

This document explains how to set up Visual Studio Code and your development environment for **Phase 2 – Group 112**.  
Follow these steps carefully to ensure the project runs correctly.

---

## 1. Clone the repository

```bash
git clone https://github.com/rsierrav/Phase2_Group112.git
cd Phase2_Group112
```

You may also use GitHub Desktop if you prefer a graphical workflow.

---

## 2. Create a virtual environment

```bash
python -m venv .venv
```

This creates a `.venv/` folder inside the project directory.  
It stores all Python packages locally and is already ignored by Git.

---

## 3. Activate the virtual environment

### On Windows (Git Bash)

```bash
source .venv/Scripts/activate
```

### On Windows (PowerShell)

```powershell
.venv\Scripts\Activate.ps1
```

### On macOS / Linux

```bash
source .venv/bin/activate
```

When the environment is active, the terminal prompt will include:
`(.venv) C:\Users\...\Phase2_Group112>`

Always make sure `(.venv)` appears before running project commands.

---

## 4. Install development dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt 2>/dev/null || true
pip install pytest pytest-cov black mypy
```

This installs:

- **pytest** – testing framework
- **black** – code formatter
- **mypy** – static type checker

---

## 5. Developer helper scripts

The `scripts/` directory includes shortcuts for common tasks.

| Script                | Purpose                         |
| --------------------- | ------------------------------- |
| `./scripts/test.sh`   | Run pytest with coverage        |
| `./scripts/lint.sh`   | Run Black (check only) and Mypy |
| `./scripts/format.sh` | Auto-format all code with Black |

Run scripts from the project root:

```bash
./scripts/test.sh
```

---

## 6. Configure VS Code

1. Open the project folder in VS Code.
2. Press **Ctrl + Shift + P → Python: Select Interpreter**, then choose the one inside `.venv`.
3. Install these extensions:
   - **Python** (ms-python.python)
   - **Pylance** (ms-python.vscode-pylance)
   - **GitHub Actions** (GitHub.vscode-github-actions)

### Optional: `.vscode/settings.json`

To enable automatic formatting on save:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}\\.venv\\Scripts\\python.exe",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["-q"],
  "python.analysis.typeCheckingMode": "basic",
  "editor.formatOnSave": true
}
```

---

## 7. Run checks manually

Format code:

```bash
./scripts/format.sh
```

Lint and type-check:

```bash
./scripts/lint.sh
```

Run tests:

```bash
./scripts/test.sh
```

All 175 tests should pass locally before committing.

---

## 8. Continuous Integration (CI/CD)

GitHub Actions automatically runs on every push or pull request to `main` or `develop`.

It performs:

1. **Black --check .** – verify code formatting
2. **Mypy .** – type checking
3. **Pytest --cov** – run tests and collect coverage

Results appear in the **Actions** tab.  
Branch protection requires all checks to pass before merging.

---

## 9. Access ECE servers

If you need to connect to Purdue ECE servers:

```bash
ssh yourusername@eceprog.ecn.purdue.edu
```

When prompted for a password, include “,push” for Duo authentication:

```bash
yourPassword,push
```

---

Reminder: Always activate the virtual environment, run tests before committing, and push changes through feature branches with pull requests.
