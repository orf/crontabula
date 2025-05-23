import datetime
import itertools

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
    assert next_iteration == datetime.datetime(2022, 4, 4, 3, 0)


@pytest.mark.freeze_time("2022-03-31 23:00")
def test_month_end():
    crontab = crontabula.parse("0 20 * * *")
    assert crontab.next == datetime.datetime(2022, 4, 1, 20)


@pytest.mark.freeze_time("2022-05-09")
def test_day_of_month():
    crontab = crontabula.parse("0 0 1 * *")
    assert crontab.next == datetime.datetime(2022, 6, 1)


@pytest.mark.freeze_time("2022-04-01")
def test_start():
    crontab = crontabula.parse("15 3 * * *")
    now = datetime.datetime.now()

    date_times = crontab.date_times(start=now - datetime.timedelta(days=2))
    assert list(itertools.islice(date_times, 4)) == [
        datetime.datetime(2022, 3, 30, 3, 15),
        datetime.datetime(2022, 3, 31, 3, 15),
        datetime.datetime(2022, 4, 1, 3, 15),
        datetime.datetime(2022, 4, 2, 3, 15),
    ]


@pytest.mark.freeze_time("2022-04-01 10:30")
def test_minutes():
    crontab = crontabula.parse("*/5 * * * *")

    date_times = crontab.date_times()
    assert list(itertools.islice(date_times, 12)) == [
        datetime.datetime(2022, 4, 1, 10, 30),
        datetime.datetime(2022, 4, 1, 10, 35),
        datetime.datetime(2022, 4, 1, 10, 40),
        datetime.datetime(2022, 4, 1, 10, 45),
        datetime.datetime(2022, 4, 1, 10, 50),
        datetime.datetime(2022, 4, 1, 10, 55),
        datetime.datetime(2022, 4, 1, 11, 0),
        datetime.datetime(2022, 4, 1, 11, 5),
        datetime.datetime(2022, 4, 1, 11, 10),
        datetime.datetime(2022, 4, 1, 11, 15),
        datetime.datetime(2022, 4, 1, 11, 20),
        datetime.datetime(2022, 4, 1, 11, 25),
    ]

    # Check that the minutes skipped on the initial day are not skipped
    # in subsequent days.
    date_times = crontab.date_times(datetime.datetime(2022, 4, 2, 10, 0))
    assert list(itertools.islice(date_times, 12)) == [
        datetime.datetime(2022, 4, 2, 10, 0),
        datetime.datetime(2022, 4, 2, 10, 5),
        datetime.datetime(2022, 4, 2, 10, 10),
        datetime.datetime(2022, 4, 2, 10, 15),
        datetime.datetime(2022, 4, 2, 10, 20),
        datetime.datetime(2022, 4, 2, 10, 25),
        datetime.datetime(2022, 4, 2, 10, 30),
        datetime.datetime(2022, 4, 2, 10, 35),
        datetime.datetime(2022, 4, 2, 10, 40),
        datetime.datetime(2022, 4, 2, 10, 45),
        datetime.datetime(2022, 4, 2, 10, 50),
        datetime.datetime(2022, 4, 2, 10, 55),
    ]


@pytest.mark.freeze_time("2022-12-31 23:59:59")
def test_year():
    crontab = crontabula.parse("0 0 * 4 *")
    assert crontab.next == datetime.datetime(2023, 4, 1)


@pytest.mark.parametrize(
    "cron_day_of_week, py_day_of_week",
    [
        (0, 6),  # Sunday
        (1, 0),  # Monday
        (2, 1),  # Tuesday
        (3, 2),  # Wednesday
        (4, 3),  # Thursday
        (5, 4),  # Friday
        (6, 5),  # Saturday
    ],
)
@pytest.mark.freeze_time("2022-01-01")
def test_day_of_week(cron_day_of_week, py_day_of_week):
    crontab = crontabula.parse(f"0 0 * 2 {cron_day_of_week}")
    assert crontab.next.weekday() == py_day_of_week

@pytest.mark.parametrize(
    "cron_day_of_week, py_day_of_week",
    [
        ("SUN", 6),  # Sunday
        ("MON", 0),  # Monday
        ("TUE", 1),  # Tuesday
        ("WED", 2),  # Wednesday
        ("THU", 3),  # Thursday
        ("FRI", 4),  # Friday
        ("SAT", 5),  # Saturday
    ],
)
def test_text_day_of_week(cron_day_of_week, py_day_of_week):
    # Test text day of week representations
    crontab = crontabula.parse(f"0 0 * 2 {cron_day_of_week}")
    assert crontab.next.weekday() == py_day_of_week


@pytest.mark.freeze_time("2022-01-01")
def test_day_of_week_and_month():
    # Comments come from https://man7.org/linux/man-pages/man1/crontab.1p.html

    # If month, day of month, and day of week are all <asterisk> characters,
    # every day shall be matched.
    crontab = crontabula.parse("0 0 * * *")
    assert list(itertools.islice(crontab.dates(), 31)) == [
        datetime.date(2022, 1, day) for day in range(1, 32)
    ]

    # If either the month or day of month is specified as an element or list,
    # but the day of week is an <asterisk>, the month and day of month fields
    # shall specify the days that match.
    crontab = crontabula.parse("0 0 3 * *")
    assert list(itertools.islice(crontab.dates(), 2)) == [
        datetime.date(2022, 1, 3),
        datetime.date(2022, 2, 3),
    ]
    crontab = crontabula.parse("0 0 * 2 *")
    assert list(itertools.islice(crontab.dates(), 2)) == [
        datetime.date(2022, 2, 1),
        datetime.date(2022, 2, 2),
    ]
    crontab = crontabula.parse("0 0 3 2 *")
    assert list(itertools.islice(crontab.dates(), 2)) == [
        datetime.date(2022, 2, 3),
        datetime.date(2023, 2, 3),
    ]

    # If both month and day of month are specified as an <asterisk>, but day of
    # week is an element or list, then only the specified days of the week match.
    crontab = crontabula.parse("0 0 * * 5")
    assert list(itertools.islice(crontab.dates(), 2)) == [
        datetime.date(2022, 1, 7),
        datetime.date(2022, 1, 14),
    ]

    # Test day of week as text instead of number
    #   at midnight
    crontab = crontabula.parse("0 0 * * FRI")
    assert list(itertools.islice(crontab.dates(), 2)) == [
        datetime.date(2022, 1, 7),
        datetime.date(2022, 1, 14),
    ]

    # Finally, if either the month or day of month is specified as an element
    # or list, and the day of week is also specified as an element or list,
    # then any day matching either the month and day of month, or the day of
    # week, shall be matched.
    crontab = crontabula.parse("0 0 3 * 5")
    assert list(itertools.islice(crontab.dates(), 7)) == [
        datetime.date(2022, 1, 3),
        datetime.date(2022, 1, 7),
        datetime.date(2022, 1, 14),
        datetime.date(2022, 1, 21),
        datetime.date(2022, 1, 28),
        datetime.date(2022, 2, 3),
        datetime.date(2022, 2, 4),
    ]
    crontab = crontabula.parse("0 0 * 2 5")
    assert list(itertools.islice(crontab.dates(), 5)) == [
        datetime.date(2022, 2, 4),
        datetime.date(2022, 2, 11),
        datetime.date(2022, 2, 18),
        datetime.date(2022, 2, 25),
        datetime.date(2023, 2, 3),
    ]
    crontab = crontabula.parse("0 0 3 2 5")
    assert list(itertools.islice(crontab.dates(), 6)) == [
        datetime.date(2022, 2, 3),
        datetime.date(2022, 2, 4),
        datetime.date(2022, 2, 11),
        datetime.date(2022, 2, 18),
        datetime.date(2022, 2, 25),
        datetime.date(2023, 2, 3),
    ]
