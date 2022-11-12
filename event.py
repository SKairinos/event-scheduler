from __future__ import annotations
import typing as t
from datetime import datetime as DateTime
from datetime import date as Date
from datetime import time as Time
import re

from pydantic import Field, validator, root_validator

from date_time_span import DateTimeSpan


class Event(DateTimeSpan):
    """A named datetime span. This can be thought of as a calendar appointment."""

    # autopep8: off
    class InvalidWeekDayError(DateTimeSpan.Error): pass
    class InvalidTimeError(DateTimeSpan.Error): pass
    class InThePastError(DateTimeSpan.Error): pass
    class StartOfDayError(DateTimeSpan.Error): pass
    class EndOfDayError(DateTimeSpan.Error): pass
    class InvalidFormatError(DateTimeSpan.Error): pass
    class InvalidDateTimeFormatError(InvalidFormatError): pass
    class TimeDeltaTooLargeError(DateTimeSpan.Error): pass
    # autopep8: on

    name: str = Field(min_length=1)

    # Setting to control which weekdays an event can be created for. 0=Monday -> 6=Sunday.
    _valid_weekdays = [0, 1, 2, 3, 4]
    # Setting to control what time of day events may start at the earliest.
    _start_of_day = Time(hour=9, minute=0)
    # Setting to control what time of day events may end at the latest.
    _end_of_day = Time(hour=18, minute=0)

    @validator('start', 'end')
    def valid_weekday(cls, value: DateTime):
        """Validate start and end are on a valid weekday."""
        if not value.weekday() in cls._valid_weekdays:
            raise cls.InvalidWeekDayError('Dates must be between Monday and Friday')
        return value

    @validator('start', 'end')
    def valid_time(cls, value: DateTime):
        """Validate start and end times are between the start and end of the day."""
        if not (cls._start_of_day <= value.time() <= cls._end_of_day):
            raise cls.InvalidTimeError('Times must be between 9:00 and 18:00')
        return value

    @validator('start', 'end')
    def not_in_the_past(cls, value: DateTime):
        """Validate start and end times are not in the past."""
        if value < DateTime.now():
            raise cls.InThePastError('Date and times cannot be in the past')
        return value

    @validator('start')
    def not_end_of_day(cls, value: DateTime):
        """Validate start is not at the end of the day."""
        if value.time() == cls._end_of_day:
            raise cls.EndOfDayError('Cannot start an event at the end of the day')
        return value

    @validator('end')
    def not_start_of_day(cls, value: DateTime):
        """Validate end is not at the start of the day."""
        if value.time() == cls._start_of_day:
            raise cls.StartOfDayError('Cannot end an event at the start of the day')
        return value

    @root_validator(pre=True)
    def lte_max_timedelta(cls, values: t.Dict[str, t.Any]):
        """Validate the timedelta between start and end doesn't exceed the max."""
        start: t.Optional[DateTime] = values.get('start')
        end: t.Optional[DateTime] = values.get('end')
        if start is not None and end is not None:
            today = Date.today()
            start_of_day = DateTime.combine(today, cls._start_of_day)
            end_of_day = DateTime.combine(today, cls._end_of_day)
            if end - start > end_of_day - start_of_day:
                raise cls.TimeDeltaTooLargeError('The timedelta between start and end is too large')
        return values

    def __str__(self) -> str:
        return super().__str__() + ' - ' + self.name

    def __eq__(self, event: Event) -> bool:
        return super().__eq__(event) and self.name == event.name

    @classmethod
    def fields_from_str(cls, event: str):
        """Extracts the fields needed to instantiate an event from a string. 

        :param event: The event in string format.
        :raises cls.InvalidFormatError: If the string is not in the expected format.
        :raises cls.InvalidDateTimeFormatError: If the start and end are not in the expected format.
        :return: A dict with the named fields needed to create an event. event = Event(**fields). 
        """
        # Match event pattern.
        match = re.match(r'(.+)->(.+)-(.+)', event)
        if not match:
            raise cls.InvalidFormatError(
                'Expected format: "<start_date> -> <end_date> - <event_name>"'
            )

        # Get event fields.
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
