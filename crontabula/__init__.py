import dataclasses
from typing import List, Iterator, Optional
import datetime
import calendar

__all__ = ["Crontab", "parse", "InvalidExpression"]


# From https://en.wikipedia.org/wiki/Cron#Nonstandard_predefined_scheduling_definitions

MACROS = {
    "@yearly": "0 0 1 1 *",
    "@annually": "0 0 1 1 *",
    "@monthly": "0 0 1 * *",
    "@weekly": "0 0 * * 0",
    "@daily": "0 0 * * *",
    "@midnight": "0 0 * * *",
    "@hourly": "0 * * * *",
}


class InvalidExpression(ValueError):
    pass


@dataclasses.dataclass(frozen=True)
class Crontab:
    minutes: List[int]
    hours: List[int]
    day_of_month: List[int]
    months: List[int]
    day_of_week: List[int]
    day_of_month_asterisk: bool
    day_of_week_asterisk: bool

    @property
    def next(self) -> datetime.datetime:
        """
        Return the next time at which this crontab should execute

        >>> crontab = parse("*/10 * * * *")
        >>> crontab.next
        datetime.datetime(...)
        """
        return next(self.date_times())

    def date_times(
        self, start: Optional[datetime.datetime] = None
    ) -> Iterator[datetime.datetime]:
        """
        Infinitely yield future points in time that this crontab expression points to. For example:

        >>> import itertools
        >>> crontab = parse("*/10 * * * *")
        >>> list(itertools.islice(crontab.date_times(), 3))
        [datetime.datetime(...), datetime.datetime(...), datetime.datetime(...)]
        """
        anchor = start if start else datetime.datetime.now()
        anchor_date = anchor.date()

        for day in self.dates(anchor_date):
            is_start_day = day == anchor_date

            for hour in self.hours:
                is_start_hour = is_start_day and hour == anchor.hour

                if is_start_day and hour < anchor.hour:
                    continue

                for minute in self.minutes:
                    if is_start_hour and minute < anchor.minute:
                        continue

                    yield datetime.datetime(
                        year=day.year,
                        month=day.month,
                        day=day.day,
                        hour=hour,
                        minute=minute,
                    )

    def dates(self, start: Optional[datetime.date] = None) -> Iterator[datetime.date]:
        """
        Infinitely yield future dates that this crontab expression points to. For example:

        >>> import itertools
        >>> crontab = parse("*/10 * * * *")
        >>> list(itertools.islice(crontab.dates(), 3))
        [datetime.date(...), datetime.date(...), datetime.date(...)]
        """
        cal = calendar.Calendar()
        anchor = start if start else datetime.date.today()
        while True:
            for month in self.months:
                if month < anchor.month:
                    continue

                for day_of_month, day_of_week in cal.itermonthdays2(anchor.year, month):
                    # itermonthdays yields all days required to get a full week,
                    # but those outside the current month are 0
                    if day_of_month == 0:
                        continue

                    if month == anchor.month and day_of_month < anchor.day:
                        continue

                    day_of_month_match = day_of_month in self.day_of_month
                    day_of_week_match = (
                        _day_of_week_to_cron(day_of_week) in self.day_of_week
                    )

                    if self.day_of_week_asterisk:
                        if not day_of_month_match:
                            continue
                    elif self.day_of_month_asterisk:
                        if not day_of_week_match:
                            continue
                    else:
                        if not day_of_month_match and not day_of_week_match:
                            continue

                    yield datetime.date(anchor.year, month, day_of_month)
            anchor = datetime.date(year=anchor.year + 1, month=1, day=1)


def parse(expression: str) -> Crontab:
    """
    Parse a crontab expression into a Crontab object.

    >>> parse("*/10 * * * *")
    Crontab(...)
    """
    # Resolve macros (@hourly etc) to equivalent cron expressions
    expression = MACROS.get(expression, expression)

    parts = expression.split(" ")
    if len(parts) != 5:
        raise InvalidExpression(f'"{expression}" does not have 5 components')

    minute_expr, hour_expr, day_month_expr, month_expr, _day_week_expr = parts

    # Handle day of week abbreviations, such as TUE
    day_week_expr = _handle_text_day_week(day_week_expr=_day_week_expr)

    minutes = _expression_to_list(minute_expr, max_value=59)
    hours = _expression_to_list(hour_expr, max_value=23)
    day_months = _expression_to_list(day_month_expr, max_value=31, min_value=1)
    months = _expression_to_list(month_expr, max_value=12, min_value=1)
    day_weeks = _expression_to_list(day_week_expr, max_value=6)

    return Crontab(
        minutes,
        hours,
        day_months,
        months,
        day_weeks,
        day_month_expr == "*",
        day_week_expr == "*",
    )

def _handle_text_day_week(day_week_expr: str) -> str:
    # convert day of week text representations, such as TUE to
    # numerical format.

    # This could be improved for silly cases such as checking for
    # invalid strings like SUNMONTUE, but that would probably require
    # a regex because SUN-TUE and SUN,MON,TUE are valid
    day_week_expr = day_week_expr.replace("SUN", "0")
    day_week_expr = day_week_expr.replace("MON", "1")
    day_week_expr = day_week_expr.replace("TUE", "2")
    day_week_expr = day_week_expr.replace("WED", "3")
    day_week_expr = day_week_expr.replace("THU", "4")
    day_week_expr = day_week_expr.replace("FRI", "5")
    day_week_expr = day_week_expr.replace("SAT", "6")
    return day_week_expr

def _expression_to_list(
    expr: str, max_value: int, *, min_value: int = 0, step: int = 1
) -> List[int]:
    # Simple recursive crontab expression parser.

    # Expressions can be delimited by commas. If this is the case call `_expression_to_list` with each
    # sub-expression, then combine and sort the results into a single list.
    if "," in expr:
        values = {
            minute
            for sub_expr in expr.split(",")
            for minute in _expression_to_list(
                sub_expr, max_value, min_value=min_value, step=step
            )
        }
        return list(sorted(values))
    elif expr == "*":
        # Return all possible values
        return list(range(min_value, max_value + 1, step))
    elif expr.isnumeric():
        # Return the single numeric value
        return [_try_int(expr, max_value=max_value, min_value=min_value)]
    elif "/" in expr:
        # The rhs of an expression containing a / is the "step" value, i.e `*/3` means
        # every 3 minutes
        lhs, rhs = expr.split("/")
        rhs_step = _try_int(rhs, max_value=max_value, min_value=min_value)
        return _expression_to_list(lhs, max_value, step=rhs_step, min_value=min_value)
    elif "-" in expr:
        # Expressions containing - represent two values, x-y. x must be less than y, but this
        # isn't currently checked.
        range_start, range_end = expr.split("-")
        return list(
            range(
                _try_int(range_start, max_value, min_value),
                _try_int(range_end, max_value, min_value) + 1,
                step,
            )
        )

    raise InvalidExpression(f"Invalid expression: {expr}")


def _try_int(v, max_value: int, min_value: int) -> int:
    try:
        result = int(v)
    except Exception as e:
        raise InvalidExpression(f"{v} is not an integer") from e

    if result < 0 or min_value > result or max_value < result:
        raise InvalidExpression(
            f"{result} is greater than {max_value} or less than {min_value}"
        )

    return result


def _day_of_week_to_cron(day_of_week: int):
    """Convert Python day-of-week (0 = Monday) to Cron (0 = Sunday)"""
    return (day_of_week + 1) % 7
