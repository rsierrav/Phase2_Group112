from typing import Any, Dict, Optional
from .protocol import Metric


class RampUpTime(Metric):
    def __init__(self) -> None:
        self.score: float = 0.0
        self.latency: float = 0.0

    def get_description(self, parsed_data: Dict[str, Any]) -> str:
        description = parsed_data.get("description", "")
        if not description:
            metadata = parsed_data.get("metadata", {})
            description = metadata.get("description", "")

        if not description:
            card_data = parsed_data.get("cardData", {})
            description = card_data.get("model_description", "") or card_data.get("description", "")
            if not description:
                metadata = parsed_data.get("metadata", {})
                card_data = metadata.get("cardData", {})
                description = card_data.get("model_description", "") or card_data.get(
                    "description", ""
                )

        return description

    def has_quick_start_guide(self, parsed_data: Dict[str, Any]) -> bool:
        description = self.get_description(parsed_data).lower()
        quick_start_indicators = [
            "quick start",
            "getting started",
            "quickstart",
            "installation",
            "usage",
            "example",
            "tutorial",
            "how to use",
        ]

        if any(indicator in description for indicator in quick_start_indicators):
            return True

        siblings = parsed_data.get("siblings", [])
        if not siblings:
            metadata = parsed_data.get("metadata", {})
            siblings = metadata.get("siblings", [])

        quick_start_files = [
            "quickstart",
            "getting_started",
            "tutorial",
            "example",
            "demo",
            "usage",
            "install",
        ]

        for sibling in siblings:
            if isinstance(sibling, dict):
                filename = sibling.get("rfilename", "").lower()
                if any(qs_file in filename for qs_file in quick_start_files):
                    return True

        return False

    def has_installation_instructions(self, parsed_data: Dict[str, Any]) -> bool:
        description = self.get_description(parsed_data).lower()
        install_indicators = [
            "pip install",
            "conda install",
            "npm install",
            "yarn add",
            "installation",
            "install",
            "setup",
            "requirements",
        ]

        if any(indicator in description for indicator in install_indicators):
            return True

        tags = parsed_data.get("tags", [])
        if not tags:
            metadata = parsed_data.get("metadata", {})
            tags = metadata.get("tags", [])

        if "transformers" in tags:
            return True

        siblings = parsed_data.get("siblings", [])
        if not siblings:
            metadata = parsed_data.get("metadata", {})
            siblings = metadata.get("siblings", [])

        install_files = [
            "requirements.txt",
            "package.json",
            "setup.py",
            "pyproject.toml",
            "environment.yml",
            "dockerfile",
            "makefile",
        ]

        for sibling in siblings:
            if isinstance(sibling, dict):
                filename = sibling.get("rfilename", "").lower()
                if any(install_file in filename for install_file in install_files):
                    return True

        return False

    def has_runnable_examples(self, parsed_data: Dict[str, Any]) -> bool:
        widget_data = parsed_data.get("widgetData", [])
        if widget_data:
            return True

        metadata = parsed_data.get("metadata", {})
        widget_data = metadata.get("widgetData", [])
        if widget_data:
            return True

        transformers_info = parsed_data.get(
            "transformersInfo", metadata.get("transformersInfo", {})
        )
        if transformers_info.get("auto_model"):
            return True

        siblings = parsed_data.get("siblings", [])
        if not siblings:
            metadata = parsed_data.get("metadata", {})
            siblings = metadata.get("siblings", [])

        example_files = [".py", ".ipynb", "example", "demo", "sample"]

        for sibling in siblings:
            if isinstance(sibling, dict):
                filename = sibling.get("rfilename", "").lower()
                if any(ex_file in filename for ex_file in example_files):
                    return True

        return False

    def has_minimal_dependencies(self, parsed_data: Dict[str, Any]) -> bool:
        tags = parsed_data.get("tags", [])
        if not tags:
            metadata = parsed_data.get("metadata", {})
            tags = metadata.get("tags", [])

        lightweight_indicators = [
            "transformers",
            "diffusers",
            "sentence-transformers",
            "sklearn",
            "numpy",
            "pytorch",
            "tensorflow",
        ]

        framework_count = sum(
            1 for tag in tags if any(lib in tag.lower() for lib in lightweight_indicators)
        )

        if framework_count > 0:
            return True

        description = self.get_description(parsed_data).lower()
        standalone_indicators = [
            "no dependencies",
            "standalone",
            "zero dependencies",
            "minimal setup",
            "plug and play",
        ]

        if any(indicator in description for indicator in standalone_indicators):
            return True

        return False

    def get_model_complexity(self, parsed_data: Dict[str, Any]) -> str:
        tags = parsed_data.get("tags", [])
        if not tags:
            metadata = parsed_data.get("metadata", {})
            tags = metadata.get("tags", [])

        size_indicators = {
            "large": ["large", "xl", "big", "giant"],
            "medium": ["medium", "base", "standard"],
            "small": ["small", "mini", "tiny", "micro", "nano"],
        }

        for size, indicators in size_indicators.items():
            if any(indicator in tag.lower() for tag in tags for indicator in indicators):
                return size

        description = self.get_description(parsed_data).lower()
        if any(word in description for word in ["billion", "parameters", "large-scale"]):
            return "large"
        elif any(word in description for word in ["lightweight", "efficient", "fast"]):
            return "small"

        return "medium"

    def has_clear_documentation(self, parsed_data: Dict[str, Any]) -> bool:
        description = self.get_description(parsed_data)

        tags = parsed_data.get("tags", [])
        if not tags:
            metadata = parsed_data.get("metadata", {})
            tags = metadata.get("tags", [])

        known_architectures = ["bert", "distilbert", "gpt", "whisper", "roberta", "t5"]
        is_known_architecture = any(
            arch in tag.lower() for tag in tags for arch in known_architectures
        )

        min_length = 50 if is_known_architecture else 100

        if not description or len(description.strip()) < min_length:
            siblings = parsed_data.get("siblings", [])
            if not siblings:
                metadata = parsed_data.get("metadata", {})
                siblings = metadata.get("siblings", [])

            doc_files = ["README.md", "README.txt", "README.rst", "docs/", "documentation"]

            for sibling in siblings:
                if isinstance(sibling, dict):
                    filename = sibling.get("rfilename", "").lower()
                    if any(doc_file.lower() in filename for doc_file in doc_files):
                        return True
            return False

        return True

    def get_data(self, parsed_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not parsed_data:
            return None

        result = {
            "category": parsed_data.get("category", ""),
            "has_quick_start_guide": self.has_quick_start_guide(parsed_data),
            "has_installation_instructions": self.has_installation_instructions(parsed_data),
            "has_runnable_examples": self.has_runnable_examples(parsed_data),
            "has_minimal_dependencies": self.has_minimal_dependencies(parsed_data),
            "model_complexity": self.get_model_complexity(parsed_data),
            "has_clear_documentation": self.has_clear_documentation(parsed_data),
            "description_length": len(self.get_description(parsed_data)),
            "tags": parsed_data.get("tags", []) or parsed_data.get("metadata", {}).get("tags", []),
        }

        return result

    def calculate_score(self, data: Optional[Dict[str, Any]]) -> None:
        if not data:
            self.score = 0.0
            return

        score = 0.0
        debug_info = []

        if data["has_clear_documentation"]:
            if data["description_length"] > 300:
                score += 0.30
                debug_info.append("docs_long: +0.30")
            elif data["description_length"] > 150:
                score += 0.25
                debug_info.append("docs_medium: +0.25")
            elif data["description_length"] > 100:
                score += 0.15
                debug_info.append("docs_short: +0.15")
            else:
                score += 0.10
                debug_info.append("docs_minimal: +0.10")
        else:
            debug_info.append("docs: 0")

        if data["has_quick_start_guide"]:
            score += 0.25
            debug_info.append("quick_start: +0.25")
        else:
            debug_info.append("quick_start: 0")

        if data["has_installation_instructions"]:
            score += 0.20
            debug_info.append("install: +0.20")
        else:
            debug_info.append("install: 0")

        if data["has_runnable_examples"]:
            score += 0.15
            debug_info.append("examples: +0.15")
        else:
            debug_info.append("examples: 0")

        if data["has_minimal_dependencies"]:
            score += 0.10
            debug_info.append("deps: +0.10")
        else:
            debug_info.append("deps: 0")

        complexity = data["model_complexity"]
        if complexity == "small":
            score += 0.05
        elif complexity == "large":
            score -= 0.05

        category = data["category"]
        if category == "DATASET":
            score += 0.05
            debug_info.append("dataset_bonus: +0.05")
        elif category == "CODE":
            if not data["has_runnable_examples"]:
                score -= 0.05
                debug_info.append("code_penalty: -0.05")

        self.score = min(score, 1.0)

    def get_score(self) -> float:
        return self.score

    def get_latency(self) -> float:
        return self.latency
