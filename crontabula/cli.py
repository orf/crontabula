import datetime
import typing

import click
from . import parse


@click.command()
@click.argument("expression")
def cli(expression):
    result = parse(expression)

    for name, values in [
        ("minute", result.minutes),
        ("hour", result.hours),
        ("day of month", result.day_of_month),
        ("month", result.months),
        ("day of week", result.day_of_week),
    ]:
        values = " ".join(str(v) for v in values)
        print(f"{name:<14} {values}")

    next_row = "next time"
    next_time = result.next
    next_time_delta = next_time - datetime.datetime.now()
    next_value = f"{next_time} (in {next_time_delta})"
    print(f"{next_row:<14} {next_value}")
