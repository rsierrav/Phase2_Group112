import os
import time
from typing import Any, Dict, List, Optional
import requests
from .protocol import Metric

# GitHub trees API to list repository files
GH_TREE_API = "https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1"

# Map common file extensions to language labels
EXT_LANG_MAP: Dict[str, str] = {
    # Python / notebooks
    ".py": "Python",
    ".ipynb": "Notebook",
    # C-family
    ".c": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".h": "C/C++ Header",
    ".hpp": "C/C++ Header",
    ".cu": "CUDA",
    ".cu.h": "CUDA",
    # Java / JVM
    ".java": "Java",
    ".kt": "Kotlin",
    ".scala": "Scala",
    ".gradle": "Gradle",
    # JavaScript / TypeScript / Node
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    # Web / scripting
    ".sh": "Shell",
    ".ps1": "PowerShell",
    # R / Julia
    ".r": "R",
    ".jl": "Julia",
    # Go / Rust / C#
    ".go": "Go",
    ".rs": "Rust",
    ".cs": "C#",
    # PHP / Ruby / Swift / Objective-C / MATLAB
    ".php": "PHP",
    ".rb": "Ruby",
    ".swift": "Swift",
    ".m": "Objective-C_or_MATLAB",
    ".mm": "Objective-C++",
    # Others
    ".pl": "Perl",
    ".scala": "Scala",
    ".tex": "LaTeX",
}


class code_quality(Metric):
    def __init__(self):
        self.score: float = -1.0
        self.latency: float = -1.0

    def _make_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {"Accept": "application/vnd.github.v3+json"}
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"token {token}"
        return headers

    def _fetch_repo_tree(
        self, repo_path: str, branch: str = "HEAD"
    ) -> Optional[List[Dict[str, Any]]]:
        url = GH_TREE_API.format(repo=repo_path, branch=branch)
        try:
            resp = requests.get(url, headers=self._make_headers(), timeout=10)
            if resp.status_code == 200:
                payload = resp.json()
                return payload.get("tree", [])
            return None
        except Exception:
            return None

    def _classify_by_extension(self, path: str) -> Optional[str]:
        """
        Return language label for the given file path based on its extension.
        """
        path = path.lower()
        for ext, lang in EXT_LANG_MAP.items():
            if path.endswith(ext):
                return lang
        return None

    def _is_test_file(self, path: str) -> bool:
        """
        Check if a file path represents a test file that should be excluded from language counts.
        Examples and documentation should NOT be excluded.
        """
        return (
            path.startswith("tests/")
            or "/tests/" in path
            or path.startswith("test/")
            or "/test/" in path
            or path.startswith("spec/")
            or "/spec/" in path
            or path.startswith("test_")
            or "/test_" in path
            or path.endswith("_test.py")
            or path.endswith("test.py")
            or path.endswith("_spec.rb")
            or path.endswith(".spec.js")
            or path.endswith(".test.js")
        )

    def get_data(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract repository evidence from CODE entry,
        or from MODEL entry with a code_url.

        Returns:
        {
            "has_tests": bool,
            "has_ci": bool,
            "has_lint_config": bool,
            "language_counts": {lang: count, ...},
            "total_code_files": int,
            "has_readme": bool,
            "has_packaging": bool,
        }
        """
        category = parsed_data.get("category", "")
        url = parsed_data.get("url", "")
        code_url = parsed_data.get("code_url", "")

        # Determine if we have a GitHub repo to check
        repo_url = None
        if category == "CODE" and isinstance(url, str) and "github.com" in url:
            repo_url = url
        elif category == "MODEL" and isinstance(code_url, str) and "github.com" in code_url:
            repo_url = code_url

        # Default empty result
        default_result = {
            "has_tests": False,
            "has_ci": False,
            "has_lint_config": False,
            "language_counts": {},
            "total_code_files": 0,
            "has_readme": False,
            "has_packaging": False,
        }

        if not repo_url:
            return default_result

        # Extract owner/repo
        try:
            parts = repo_url.split("github.com/")[-1].split("/")
            repo_path = "/".join(parts[:2])  # owner/repo
        except Exception:
            return default_result

        tree = self._fetch_repo_tree(repo_path)
        if not tree:
            return default_result

        # Inspect file paths
        has_tests = False
        has_ci = False
        has_lint_config = False
        language_counts: Dict[str, int] = {}
        has_readme = False
        has_packaging = False

        # Packaging files across ecosystems
        packaging_files = {
            "setup.py",
            "pyproject.toml",
            "setup.cfg",
            "requirements.txt",
            "package.json",
            "pom.xml",  # maven (java)
            "build.gradle",  # gradle (java/kotlin)
            "gradle.properties",
            "Cargo.toml",  # rust
            "go.mod",  # go
            "DESCRIPTION",  # R
            "environment.yml",
            "conda.yml",
            "Makefile",
            "Pipfile",
            "poetry.lock",
            "manifest.in",
            "__init__.py",
        }

        for entry in tree:
            raw_path = entry.get("path", "") or ""
            path = raw_path.lower().lstrip("./")

            # Debug: print paths being processed
            print(f"DEBUG: Processing path: '{path}' (from raw: '{raw_path}')")

            # More test detection
            if (
                path.startswith("tests/")
                or "/tests/" in path
                or path.startswith("test/")
                or "/test/" in path
                or path.startswith("spec/")
                or "/spec/" in path
                or path.startswith("example/")
                or "/example/" in path
                or path.startswith("examples/")
                or "/examples/" in path
                or path.startswith("test_")
                or "/test_" in path
                or path.endswith("_test.py")
                or path.endswith("test.py")
                or path.endswith("_spec.rb")
                or path.endswith(".spec.js")
                or path.endswith(".test.js")
                or "unittest" in path
                or "pytest" in path
            ):
                has_tests = True
                print(f"DEBUG: Found test file: '{path}'")

            # More CI detection
            if (
                path.startswith(".github/workflows")
                or path.endswith(".travis.yml")
                or path.endswith("travis.yml")
                or ".circleci/" in path
                or path.endswith("azure-pipelines.yml")
                or path.endswith("azure-pipelines.yaml")
                or path.endswith("jenkinsfile")
                or path.endswith("drone.yml")
                or path.endswith(".yml")
                and ("ci" in path or "build" in path or "deploy" in path)
                or path.endswith(".yaml")
                and ("ci" in path or "build" in path or "deploy" in path)
                or path.startswith("ci/")
                or "/ci/" in path
                or path == "makefile"
                or path == "dockerfile"
                or path.endswith("build.sh")
                or path.endswith("build.bat")
            ):
                has_ci = True
                print(f"DEBUG: Found CI file: '{path}'")

            # More linting detection
            if (
                path
                in {
                    ".flake8",
                    "pyproject.toml",
                    "setup.cfg",
                    "tox.ini",
                    ".pylintrc",
                    "pylint.cfg",
                    ".black",
                    ".isort.cfg",
                    ".pre-commit-config.yaml",
                    ".pre-commit-config.yml",
                    "requirements-dev.txt",
                    "requirements.dev.txt",
                    ".eslintrc",
                    ".eslintrc.json",
                    ".eslintrc.js",
                    ".eslintrc.yaml",
                    ".stylelintrc",
                    ".rubocop.yml",
                    ".rubocop.yml",
                    "ruff.toml",
                }
                or path.endswith("lint.py")
                or path.endswith("format.py")
                or "linting" in path
                or "formatting" in path
            ):
                has_lint_config = True
                print(f"DEBUG: Found lint config file: '{path}'")

            # More README detection
            if (
                path.startswith("readme")
                or path in {"readme.md", "readme.rst", "readme.txt", "readme"}
                or path == "index.md"
                or path == "home.md"
            ):
                has_readme = True
                print(f"DEBUG: Found README file: '{path}'")

            # More packaging detection
            if path in packaging_files or any(path.endswith(f) for f in packaging_files):
                has_packaging = True
                print(f"DEBUG: Found packaging file: '{path}'")

            # Classify file by extension and increment language counts
            lang = self._classify_by_extension(path)
            if lang:
                # Only count non-test files for language statistics
                if not self._is_test_file(path):
                    language_counts[lang] = language_counts.get(lang, 0) + 1
                    print(f"DEBUG: Counted language file: '{path}' as {lang}")
                else:
                    print(f"DEBUG: Excluded test file from language count: '{path}'")

        total_code_files = sum(language_counts.values())

        print(f"DEBUG: Final results - has_lint_config: {has_lint_config}")
        print(f"DEBUG: Language counts: {language_counts}")

        return {
            "has_tests": has_tests,
            "has_ci": has_ci,
            "has_lint_config": has_lint_config,
            "language_counts": language_counts,
            "total_code_files": total_code_files,
            "has_readme": has_readme,
            "has_packaging": has_packaging,
        }

    def calculate_score(self, data: Any) -> None:
        """
        Compute a weighted score in [0,1] from the inventory returned by get_data.

        Weights (example):
          - tests presence: 0.30
          - CI presence:    0.25
          - lint config:    0.15
          - code files:     0.15  (scaled by total_code_files)
          - docs/packaging: 0.15

        For code files we use:
          s_code = min(1.0, total_code_files / 50.0)

        We also add a small bonus for language diversity:
          diversity_bonus = min(0.2, (num_languages / 5.0) * 0.2)
        which is folded into the code files subscore before weighting.
        """
        start = time.perf_counter()

        has_tests = bool(data.get("has_tests", False))
        has_ci = bool(data.get("has_ci", False))
        has_lint = bool(data.get("has_lint_config", False))
        lang_counts = data.get("language_counts", {}) or {}
        total_files = int(data.get("total_code_files", 0) or 0)
        has_readme = bool(data.get("has_readme", False))
        has_packaging = bool(data.get("has_packaging", False))

        # weights
        w_tests, w_ci, w_lint, w_code, w_doc_pack = 0.30, 0.25, 0.15, 0.15, 0.15

        # subscores
        s_tests = 1.0 if has_tests else 0.0
        s_ci = 1.0 if has_ci else 0.0
        s_lint = 1.0 if has_lint else 0.0

        # code files subscore: scale to 50 files as "full"
        if total_files <= 0:
            s_code = 0.0
        else:
            s_code = min(1.0, total_files / 50.0)

        # Diversity bonus (max 0.2 added to code subscore before weighting)
        num_langs = len([lang for lang, count in lang_counts.items() if count > 0])
        diversity_bonus = min(0.2, (num_langs / 5.0) * 0.2) if num_langs > 0 else 0.0
        s_code = min(1.0, s_code + diversity_bonus)

        # docs/packaging score
        if has_readme and has_packaging:
            s_doc_pack = 1.0
        elif has_readme or has_packaging:
            s_doc_pack = 0.5
        else:
            s_doc_pack = 0.0

        score = (
            w_tests * s_tests
            + w_ci * s_ci
            + w_lint * s_lint
            + w_code * s_code
            + w_doc_pack * s_doc_pack
        )

        self.score = max(0.0, min(1.0, score))

        end = time.perf_counter()
        self.latency = (end - start) * 1000.0

    def get_score(self) -> float:
        return self.score

    def get_latency(self) -> float:
        return self.latency
