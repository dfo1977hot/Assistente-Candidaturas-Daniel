from acd.domain.planner.priority import Priority


def test_priority_values():

    assert Priority.LOW == "Baixa"

    assert Priority.NORMAL == "Normal"

    assert Priority.HIGH == "Alta"

    assert Priority.CRITICAL == "Crítica"
