# Setup Guide

This document explains how to set up Visual Studio Code and your development environment for **Phase 2 – Group 112**.  
Follow these steps carefully to ensure the project runs correctly.

---

## 1. Install uv

`uv` is a fast Python package installer and project manager. Install it following the [official documentation](https://docs.astral.sh/uv/getting-started/installation/).

---

## 2. Clone the repository

```bash
git clone https://github.com/rsierrav/Phase2_Group112.git
cd Phase2_Group112
```

You may also use GitHub Desktop if you prefer a graphical workflow.

---

## 3. Set up the project environment

Create a virtual environment and install all dependencies:

```bash
uv sync
```

This command:
- Creates a `.venv/` folder inside the project directory
- Installs all dependencies from `pyproject.toml` or `requirements.txt`
- The `.venv/` folder is already ignored by Git

---

## 4. (Optional) Activate the virtual environment

You can use `uv run` to execute commands (recommended), or manually activate the virtual environment:

### On macOS / Linux

```bash
source .venv/bin/activate
```

### On Windows (Git Bash)

```bash
source .venv/Scripts/activate
```

### On Windows (PowerShell)

```powershell
.venv\Scripts\Activate.ps1
```

When activated, your terminal prompt will show `(.venv)` prefix. With an activated environment, you can run commands directly without the `uv run` prefix:

```bash
pytest --cov
black .
mypy .
```

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

Alternatively, run commands directly:

```bash
uv run pytest
uv run black .
uv run mypy .
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
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["-q"],
  "python.analysis.typeCheckingMode": "basic",
  "editor.formatOnSave": true
}
```

**Note:** On Windows, use `"${workspaceFolder}\\.venv\\Scripts\\python.exe"`

---

## 7. Run checks manually

Format code:

```bash
uv run black .
# or
./scripts/format.sh
```

Lint and type-check:

```bash
uv run black --check .
uv run mypy .
# or
./scripts/lint.sh
```

Run tests:

```bash
uv run pytest --cov
# or
./scripts/test.sh
```

All tests should pass locally before committing.

---

## 8. Adding new dependencies

To add a new package:

```bash
uv add package-name
```

To add a development dependency:

```bash
uv add --dev package-name
```

This updates your `pyproject.toml` and installs the package.

---

## 9. Continuous Integration (CI/CD)

GitHub Actions automatically runs on every push or pull request to `main` or `develop`.

**Update your CI workflow** to use `uv`:

```yaml
- name: Set up uv
  uses: astral-sh/setup-uv@v1

- name: Install dependencies
  run: uv sync

- name: Run checks
  run: |
    uv run black --check .
    uv run mypy .
    uv run pytest --cov
```

Results appear in the **Actions** tab.  
Branch protection requires all checks to pass before merging.

---

## 10. Access ECE servers

If you need to connect to Purdue ECE servers:

```bash
ssh yourusername@eceprog.ecn.purdue.edu
```

When prompted for a password, include “,push” for Duo authentication:

```bash
yourPassword,push
```

---

Reminder: Use `uv run` for commands (or activate the virtual environment with `source .venv/bin/activate`), run tests before committing, and push changes through feature branches with pull requests.
