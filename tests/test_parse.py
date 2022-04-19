import datetime

import pytest
import crontabula


@pytest.mark.parametrize(
    "expr",
    [
        "5 4 * * *",
        "5 0 * 8 *",
        "15 14 1 * *",
        "0 22 * * 1-5",
        "23 0-20/2 * * *",
        "0 0,12 1 */2 *",
        "23 0-20/2 * * *",
    ],
)
def test_parse(expr: str):
    v = crontabula.parse(expr)
    assert v is not None


@pytest.mark.parametrize(
    "expr, expected",
    [
        ("*/10", [0, 10, 20, 30, 40, 50]),
        ("0-20/10", [0, 10, 20]),
        ("0-20/10,40-50/10", [0, 10, 20, 40, 50]),
        ("0-20/10,*/10,12", [0, 10, 12, 20, 30, 40, 50]),
    ],
)
def test_expr(expr, expected):
    result = crontabula.parse(f"{expr} * * * *")
    assert result.minutes == expected, result.minutes


def test_next():
    crontab = crontabula.parse("*/10 3,6 * * 1-4")
    now = datetime.datetime.now()
    next_iteration = crontab.next
    assert next_iteration > now
