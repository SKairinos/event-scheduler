from __future__ import annotations
import typing as t
from datetime import datetime as DateTime
from datetime import date as Date
from datetime import time as Time
from itertools import groupby
import re

from pydantic import Field, validator, root_validator

from date_time_span import DateTimeSpan


class Event(DateTimeSpan):

    # autopep8: off
    class Error(ValueError):
        def __str__(self) -> str:
            return f'{self.__class__.__name__}: {super().__str__()}'
    class InvalidDayError(Error): pass
    class InvalidTimeError(Error): pass
    class StartOfDayError(Error): pass
    class EndOfDayError(Error): pass
    class StartDateNotEqualToEndDateError(Error): pass
    class InvalidFormatError(Error): pass
    class InvalidDateTimeFormatError(InvalidFormatError): pass
    # autopep8: on

    name: str = Field(min_length=1)

    _valid_days = [0, 1, 2, 3, 4]
    _start_of_day = Time(hour=9, minute=0)
    _end_of_day = Time(hour=18, minute=0)

    @validator('start', 'end')
    def valid_day(cls, value: DateTime):
        if not value.weekday() in cls._valid_days:
            raise cls.InvalidDayError('Dates must be between Monday and Friday')
        return value

    @validator('start', 'end')
    def valid_time(cls, value: DateTime):
        if not (cls._start_of_day <= value.time() <= cls._end_of_day):
            raise cls.InvalidTimeError('Times must be between 9:00 and 18:00')
        return value

    @validator('start')
    def not_end_of_day(cls, value: DateTime):
        if value.time() == cls._end_of_day:
            raise cls.EndOfDayError('Cannot start an event at the end of the day')
        return value

    @validator('end')
    def not_start_of_day(cls, value: DateTime):
        if value.time() == cls._start_of_day:
            raise cls.StartOfDayError('Cannot end an event at the start of the day')
        return value

    @root_validator(pre=True)
    def date__start_eq_end(cls, values: t.Dict[str, t.Any]):
        start: t.Optional[DateTime] = values.get('start')
        end: t.Optional[DateTime] = values.get('end')
        if start is not None and end is not None and start.date() != end.date():
            raise cls.StartDateNotEqualToEndDateError('The start and end dates must be equal')
        return values

    def __str__(self) -> str:
        return super().__str__() + ' - ' + self.name

    def __eq__(self, event: Event) -> bool:
        return super().__eq__(event) and self.name == event.name

    @classmethod
    def fields_from_str(cls, event: str):
        # Match event pattern.
        match = re.match(r'(.+)->(.+)-(.+)', event)
        if not match:
            raise cls.InvalidFormatError(
                'Expected format: "<start_date> -> <end_date> - <event_name>"'
            )

        # Get event attributes.
        start = match.group(1).strip()
        end = match.group(2).strip()
        name = match.group(3).strip()

        # Cast datetime strings to objects.
        def to_datetime(dt: str):
            try:
                return DateTime.strptime(dt, '%Y/%m/%d %H:%M')
            except ValueError as ex:
                raise cls.InvalidDateTimeFormatError(
                    'Expected format: "YYYY/MM/DD HH:mm"'
                ) from ex

        return {
            'start': to_datetime(start),
            'end': to_datetime(end),
            'name': name
        }

    @classmethod
    def from_str(cls, event: str):
        return cls(**cls.fields_from_str(event))

    @staticmethod
    def merge_date_time_spans(events: t.List[Event]):
        # Group events by date.
        def group_key(event: Event):
            return event.start.date()
        events.sort(key=group_key)
        grouped_spans = {
            date: list(events)
            for date, events in groupby(events, key=group_key)
        }

        # For each date, merge events' spans.
        merged_spans: t.Dict[Date, t.List[DateTimeSpan]] = {}
        for date, spans in grouped_spans.items():
            merged_spans[date] = []
            spans.sort()
            while spans:
                span = spans.pop(0)
                while spans:
                    merged_span = DateTimeSpan.merge(span, spans[0])
                    if merged_span is None:
                        break
                    else:
                        span = merged_span
                        spans.pop(0)
                merged_spans[date].append(span)
        return merged_spans
