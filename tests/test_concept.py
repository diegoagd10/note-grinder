from src.concept import Concept


def test_all_fields_are_present() -> None:
    c = Concept(
        filename="⏰🧠¿Cuándo es válido ignorar el diseño?",
        body="Cuando el costo de rediseñar supera el beneficio esperado.",
        tags=["Software_Design"],
        example="Un prototipo que se descartará en dos días.",
    )
    assert c.filename == "⏰🧠¿Cuándo es válido ignorar el diseño?"
    assert c.body == "Cuando el costo de rediseñar supera el beneficio esperado."
    assert c.tags == ["Software_Design"]
    assert c.example == "Un prototipo que se descartará en dos días."


def test_tags_defaults_to_empty_list() -> None:
    c = Concept(filename="🧠¿Qué es TDD?", body="Escribe el test primero.")
    assert c.tags == []


def test_example_defaults_to_empty_string() -> None:
    c = Concept(filename="🧠¿Qué es TDD?", body="Escribe el test primero.")
    assert c.example == ""


def test_instantiation_with_only_required_fields() -> None:
    c = Concept(
        filename="🏗️¿Qué es un módulo profundo?",
        body="Interfaz simple, comportamiento rico.",
    )
    assert c.filename == "🏗️¿Qué es un módulo profundo?"
    assert c.body == "Interfaz simple, comportamiento rico."


def test_equal_instances_with_same_values() -> None:
    a = Concept(filename="🧠¿Q?", body="B", tags=["T"], example="E")
    b = Concept(filename="🧠¿Q?", body="B", tags=["T"], example="E")
    assert a == b


def test_instances_with_different_values_are_not_equal() -> None:
    a = Concept(filename="🧠¿Q?", body="B")
    b = Concept(filename="🧠¿Q?", body="Different")
    assert a != b
