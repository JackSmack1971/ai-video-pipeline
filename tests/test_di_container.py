from infrastructure.di_container import DIContainer


def test_singleton_resolution() -> None:
    container = DIContainer()
    container.register_singleton("x", lambda: 1)
    assert container["x"] == 1
    assert container["x"] is container["x"]


def test_factory_resolution() -> None:
    container = DIContainer()
    counter = {"v": 0}

    def factory() -> int:
        counter["v"] += 1
        return counter["v"]

    container.register_factory("y", factory)
    assert container["y"] == 1
    assert container["y"] == 2


def test_get_with_default() -> None:
    container = DIContainer()
    assert container.get("missing") is None
    container.register_singleton("x", lambda: 5)
    assert container.get("x") == 5
