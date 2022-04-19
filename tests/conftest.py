import pytest


@pytest.fixture(autouse=True)
def freeze_time(freezer):
    freezer.move_to("2022-04-01")
    yield
