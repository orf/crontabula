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
        *crontabula.MACROS.keys(),
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


@pytest.mark.freeze_time("2022-04-01")
def test_next():
    crontab = crontabula.parse("*/10 3,6 * * 1-4")
    now = datetime.datetime.now()
    next_iteration = crontab.next
    assert next_iteration > now
    assert next_iteration == datetime.datetime(2022, 4, 1, 3, 0)


@pytest.mark.freeze_time("2022-03-31 23:00")
def test_month_end():
    crontab = crontabula.parse("0 20 * * *")
    assert crontab.next == datetime.datetime(2022, 4, 1, 20)


@pytest.mark.freeze_time("2022-05-09")
def test_day_of_month():
    crontab = crontabula.parse("0 0 1 * *")
    assert crontab.next == datetime.datetime(2022, 6, 1)
