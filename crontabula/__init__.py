import dataclasses
from typing import List, Iterable
import datetime
import calendar

__all__ = ["Crontab", "parse", "InvalidExpression"]


class InvalidExpression(ValueError):
    pass


@dataclasses.dataclass(frozen=True)
class Crontab:
    minutes: List[int]
    hours: List[int]
    day_of_month: List[int]
    months: List[int]
    day_of_week: List[int]

    @property
    def next(self) -> datetime.datetime:
        """
        Return the next time at which this crontab should execute

        >>> crontab = parse("*/10 * * * *")
        >>> crontab.next
        datetime.datetime(...)
        """
        return next(iter(self.date_times))

    @property
    def date_times(self) -> Iterable[datetime.datetime]:
        """
        Infinitely yield future points in time that this crontab expression points to. For example:

        >>> import itertools
        >>> crontab = parse("*/10 * * * *")
        >>> list(itertools.islice(crontab.date_times, 3))
        [datetime.datetime(...), datetime.datetime(...), datetime.datetime(...)]
        """
        anchor = datetime.datetime.now()
        year = anchor.year

        for day in self.dates:
            is_today = day == anchor.date()

            for hour in self.hours:
                if is_today and hour < anchor.hour:
                    continue

                for minute in self.minutes:
                    if is_today and minute < anchor.minute:
                        continue

                    dt = datetime.datetime(
                        year=year,
                        month=day.month,
                        day=day.day,
                        hour=hour,
                        minute=minute,
                    )
                    if dt.weekday() in self.day_of_week:
                        yield dt

    @property
    def dates(self) -> Iterable[datetime.date]:
        """
        Infinitely yield future dates that this crontab expression points to. For example:

        >>> import itertools
        >>> crontab = parse("*/10 * * * *")
        >>> list(itertools.islice(crontab.dates, 3))
        [datetime.date(...), datetime.date(...), datetime.date(...)]
        """
        cal = calendar.Calendar()
        anchor = datetime.date.today()
        while True:
            for month in self.months:
                if month < anchor.month:
                    continue

                for day_of_month, day_of_week in cal.itermonthdays2(anchor.year, month):
                    if month == anchor.month and day_of_month < anchor.day:
                        continue

                    if day_of_week not in self.day_of_week:
                        continue

                    yield datetime.date(anchor.year, month, day_of_month)
            anchor = datetime.date(year=anchor.year + 1, month=1, day=1)


def parse(expression: str) -> Crontab:
    """
    Parse a crontab expression into a Crontab object.

    >>> parse("*/10 * * * *")
    Crontab(...)
    """
    parts = expression.split(" ")
    if len(parts) != 5:
        raise InvalidExpression(f'"{expression}" does not have 5 components')

    minute_expr, hour_expr, day_month_expr, month_expr, day_week_expr = parts

    minutes = _expression_to_list(minute_expr, max_value=59)
    hours = _expression_to_list(hour_expr, max_value=23)
    day_months = _expression_to_list(day_month_expr, max_value=31)
    months = _expression_to_list(month_expr, max_value=12)
    day_weeks = _expression_to_list(day_week_expr, max_value=6)

    return Crontab(minutes, hours, day_months, months, day_weeks)


def _expression_to_list(expr: str, max_value: int, step: int = 1) -> List[int]:
    # Simple recursive crontab expression parser.

    # Expressions can be delimited by commas. If this is the case call `_expression_to_list` with each
    # sub-expression, then combine and sort the results into a single list.
    if "," in expr:
        values = {
            minute
            for sub_expr in expr.split(",")
            for minute in _expression_to_list(sub_expr, max_value)
        }
        return list(sorted(values))

    if expr == "*":
        # Return all possible values
        return list(range(0, max_value + 1, step))
    elif expr.isnumeric():
        # Return the single numeric value
        return [_try_int(expr, max_value=max_value)]
    elif "/" in expr:
        lhs, rhs = expr.split("/")
        rhs_step = _try_int(rhs, max_value=max_value)
        return _expression_to_list(lhs, max_value, step=rhs_step)
    elif "," in expr:
        lhs, rhs = expr.split(",")
        result = set(_expression_to_list(lhs, max_value)) | set(
            _expression_to_list(rhs, max_value)
        )
        return list(sorted(result))
    elif "-" in expr:
        range_start, range_end = expr.split("-")
        return list(
            range(
                _try_int(range_start, max_value),
                _try_int(range_end, max_value) + 1,
                step,
            )
        )

    raise RuntimeError(f"Invalid expression: {expr}")


def _try_int(v, max_value: int) -> int:
    try:
        result = int(v)
    except Exception as e:
        raise InvalidExpression(f"{v} is not an integer") from e

    if result > max_value or result < 0:
        raise InvalidExpression(f"{result} is greater than {max_value}")

    return result
