from src.concept import Concept


def test_all_four_fields_are_present() -> None:
    c = Concept(
        question="What is TDD?",
        conclusion="Test first.",
        why="Forces design.",
        example="Red-Green-Refactor",
    )
    assert c.question == "What is TDD?"
    assert c.conclusion == "Test first."
    assert c.why == "Forces design."
    assert c.example == "Red-Green-Refactor"


def test_why_defaults_to_empty_string() -> None:
    c = Concept(question="Q", conclusion="C")
    assert c.why == ""


def test_example_defaults_to_empty_string() -> None:
    c = Concept(question="Q", conclusion="C")
    assert c.example == ""


def test_instantiation_with_only_required_fields() -> None:
    c = Concept(question="What is a deep module?", conclusion="Simple interface, rich behavior.")
    assert c.question == "What is a deep module?"
    assert c.conclusion == "Simple interface, rich behavior."


def test_equal_instances_with_same_values() -> None:
    a = Concept(question="Q", conclusion="C", why="W", example="E")
    b = Concept(question="Q", conclusion="C", why="W", example="E")
    assert a == b


def test_instances_with_different_values_are_not_equal() -> None:
    a = Concept(question="Q", conclusion="C")
    b = Concept(question="Q", conclusion="Different")
    assert a != b
