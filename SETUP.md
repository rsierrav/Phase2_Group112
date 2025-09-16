# Setup Guide

This project uses **Python 3.13**, a **virtual environment** (`.venv`), and **pre-commit hooks** to ensure code consistency.  
Follow these steps to set up your development environment.

## 1. Clone the repo

```bash
git clone https://github.com/TristanG115/Team-s-Repository
cd Team-s-Repository
```

You can also use github desktop, that is what I do.


## 2. Create a virtual environment

```bash
python -m venv .venv
```

This makes a `.venv/` folder inside the repo.  
It will hold **all Python packages** for this project.
It is added to .gitignore so it will uploaded when pushed.

## 3. Activate the virtual environment

### On Windows (PowerShell)
```powershell
.venv\Scripts\Activate.ps1
```

### On macOS/Linux
```bash
source .venv/bin/activate
```

When active, your terminal prompt will show:

```
(.venv) C:\Users\...\Team-s-Repository>
```

Always make sure `(.venv)` appears before working.  


## 4. Install development dependencies

```bash
pip install -r requirements-dev.txt
```

This installs:  
- **flake8** → linter  
- **black** → code formatter  
- **pre-commit** → Git hooks  
- **pytest** → testing framework  

## 5. Install Git hooks

```bash
pre-commit install
```

Now every `git commit` will:  
- Format code with Black  
- Lint code with Flake8  

If a hook fails, fix the issue and commit again.

## 6. Configure VS Code

1. Open VS Code in this repo.  
2. Press **Ctrl+Shift+P** → *Python: Select Interpreter*.  
3. Choose the one inside `.venv`.  
4. Go to extenstions download the following
5. Flake by microsoft
6. Black by microsoft
7. ms-python.isort
7. python if you havent already

### Optional: Add `.vscode/settings.json` to enforce auto-formatting on save
## I highly reccommend we all do this step

```json
{
    "python.defaultInterpreterPath": ".venv",
    "editor.formatOnSave": true,
    "[python]": {
        "editor.defaultFormatter": "ms-python.black-formatter"
    },
    "flake8.args": [
        "--max-line-length=100"
    ],
    "isort.args": [
        "--profile",
        "black"
    ]
}
```

## 7. Run checks manually (if needed)

- Format code:
  ```bash
  black .
  ```
- Lint code:
  ```bash
  flake8 .
  ```
- Run tests:
  ```bash
  pytest
  ```

---

## 8. CI/CD on GitHub

GitHub Actions will automatically:  
- Run Black + Flake8 checks  
- Run pre-commit hooks  
- Run pytest  

You’ll see results under the **Actions** tab in the repo.

## To connect to eceprog

Download and connecto to purdue CISCO
open terminal, type

ssh username@eceprog.ecn.purdue.edu

When asked for password enter it like this

yourPassword,push

You need the ,push at the end to get duo push to connect