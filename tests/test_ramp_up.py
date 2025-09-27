import pytest
from src.metrics.ramp_up_time import RampUpTime


@pytest.fixture
def ramp_up():
    return RampUpTime()


def make_parsed_data(
    description="",
    metadata=None,
    card_data=None,
    siblings=None,
    tags=None,
    widget_data=None,
    transformers_info=None,
    category="",
):
    metadata = metadata or {}
    card_data = card_data or {}
    siblings = siblings or []
    tags = tags or []
    widget_data = widget_data or []
    transformers_info = transformers_info or {}

    return {
        "description": description,
        "metadata": metadata,
        "cardData": card_data,
        "siblings": siblings,
        "tags": tags,
        "widgetData": widget_data,
        "transformersInfo": transformers_info,
        "category": category,
    }


def test_get_description_basic(ramp_up):
    data = {"description": "Test description"}
    assert ramp_up.get_description(data) == "Test description"


def test_get_description_fallbacks(ramp_up):
    data = {
        "metadata": {},
        "cardData": {"model_description": "Model desc"},
    }
    assert ramp_up.get_description(data) == "Model desc"

    data = {
        "metadata": {"cardData": {"description": "Card desc"}},
    }
    assert ramp_up.get_description(data) == "Card desc"


@pytest.mark.parametrize(
    "desc, siblings, expected",
    [
        ("This is a quick start guide", [], True),
        ("", [{"rfilename": "quickstart.md"}], True),
        ("", [{"rfilename": "README.md"}], False),
        ("No guide here", [], False),
    ],
)
def test_has_quick_start_guide(ramp_up, desc, siblings, expected):
    data = make_parsed_data(description=desc, siblings=siblings)
    assert ramp_up.has_quick_start_guide(data) == expected


@pytest.mark.parametrize(
    "desc, tags, siblings, expected",
    [
        ("Run pip install now", [], [], True),
        ("", ["transformers"], [], True),
        ("", [], [{"rfilename": "requirements.txt"}], True),
        ("No install info", [], [], False),
    ],
)


def has_installation_instructions(self, data):
    desc = data.get("description", "").lower()
    tags = data.get("tags", [])
    siblings = data.get("siblings", [])

    if any(keyword in desc for keyword in ["install", "pip install", "setup"]):
        return True

    if "transformers" in tags:
        return True

    for sibling in siblings:
        filename = sibling.get("rfilename", "").lower()
        if filename == "requirements.txt":
            return True

    return False

@pytest.mark.parametrize(
    "widget_data, siblings, transformers_info, expected",
    [
        ([{"widget": True}], [], {}, True),
        ([], [{"rfilename": "example.py"}], {}, True),
        ([], [], {"auto_model": True}, True),
        ([], [], {}, False),
    ],
)
def test_has_runnable_examples(ramp_up, widget_data, siblings, transformers_info, expected):
    data = make_parsed_data(widget_data=widget_data, siblings=siblings, transformers_info=transformers_info)
    assert ramp_up.has_runnable_examples(data) == expected


@pytest.mark.parametrize(
    "tags, description, expected",
    [
        (["pytorch"], "", True),
        ([], "no dependencies here", True),
        ([], "something else", False),
    ],
)
def test_has_minimal_dependencies(ramp_up, tags, description, expected):
    data = make_parsed_data(tags=tags, description=description)
    assert ramp_up.has_minimal_dependencies(data) == expected


@pytest.mark.parametrize(
    "tags, description, expected",
    [
        (["large", "xl"], "", "large"),
        (["small"], "", "small"),
        ([], "large-scale model with billion parameters", "large"),
        ([], "fast and efficient", "small"),
        ([], "normal stuff", "medium"),
    ],
)
def test_get_model_complexity(ramp_up, tags, description, expected):
    data = make_parsed_data(tags=tags, description=description)
    assert ramp_up.get_model_complexity(data) == expected


@pytest.mark.parametrize(
    "description, tags, siblings, expected",
    [
        ("Short description here that is long enough to pass the minimum length for known arch.", ["bert"], [], True),
        ("Too short", [], [{"rfilename": "README.md"}], True),
        ("Too short", [], [], False),
    ],
)
def test_has_clear_documentation(ramp_up, description, tags, siblings, expected):
    data = make_parsed_data(description=description, tags=tags, siblings=siblings)
    assert ramp_up.has_clear_documentation(data) == expected


def test_get_data_structure(ramp_up):
    data = make_parsed_data(
        description="Some description",
        tags=["tag1"],
        siblings=[{"rfilename": "README.md"}],
        category="CODE",
        widget_data=[{"widget": True}],
        transformers_info={"auto_model": True},
    )
    result = ramp_up.get_data(data)
    assert isinstance(result, dict)
    assert "has_quick_start_guide" in result
    assert "description_length" in result
    assert result["tags"] == ["tag1"]


def test_calculate_score(ramp_up):
    data = {
        "has_clear_documentation": True,
        "description_length": 350,
        "has_quick_start_guide": True,
        "has_installation_instructions": True,
        "has_runnable_examples": True,
        "has_minimal_dependencies": True,
        "model_complexity": "small",
        "category": "DATASET",
        "tags": [],
    }
    ramp_up.calculate_score(data)
    assert 0.9 <= ramp_up.get_score() <= 1.0

    ramp_up.calculate_score(None)
    assert ramp_up.get_score() == 0.0

    data["model_complexity"] = "large"
    data["category"] = "CODE"
    data["has_runnable_examples"] = False
    ramp_up.calculate_score(data)
    assert ramp_up.get_score() < 1.0


def test_get_score_and_latency_initial(ramp_up):
    assert ramp_up.get_score() == 0.0
    assert ramp_up.get_latency() == 0.0

