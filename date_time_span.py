from __future__ import annotations
import typing as t
from datetime import datetime as DateTime
from datetime import timedelta as TimeDelta

from pydantic import BaseModel, Field, root_validator


class DateTimeSpan(BaseModel):

    # autopep8: off
    class StartGreaterThanOrEqualToEndError(ValueError): pass
    # autopep8: on

    start: DateTime = Field()
    end: DateTime = Field()

    @root_validator(pre=True)
    def start_lt_end(cls, values: t.Dict[str, t.Any]):
        start: t.Optional[DateTime] = values.get('start')
        end: t.Optional[DateTime] = values.get('end')
        if start is not None and end is not None and start >= end:
            raise cls.StartGreaterThanOrEqualToEndError(
                'The start cannot be greater than or equal to the end')
        return values

    def __lt__(self, span: DateTimeSpan) -> bool:
        return (self.start, self.end) < (span.start, span.end)

    def __eq__(self, span: DateTimeSpan) -> bool:
        return self.start == span.start and self.end == span.end

    def __str__(self) -> str:
        return '{start:%Y/%m/%d %H:%M} -> {end:%Y/%m/%d %H:%M}'.format(
            start=self.start,
            end=self.end
        )

    def __repr__(self) -> str:
        return str(self)

    @property
    def timedelta(self) -> TimeDelta:
        return self.end - self.start

    def overlaps_with(self, span: DateTimeSpan, equals: bool):
        return (
            span.start <= self.start <= span.end
            or span.start <= self.end <= span.end
        ) if equals else (
            span.start <= self.start < span.end
            or span.start < self.end <= span.end
        )

    @classmethod
    def merge(cls, span_1: DateTimeSpan, span_2: DateTimeSpan):
        """Merge two overlapping time spans.

        :param time_span_1: The first time span to merge.   
        :param time_span_2: The second time span to merge.
        :return: A new time span with the merged start and end.
            If the time spans are not overlapping, None is returned.   
        """
        if span_1.overlaps_with(span_2, equals=True):
            return cls(
                start=span_1.start if span_1.start <= span_2.start else span_2.start,
                end=span_1.end if span_1.end >= span_2.end else span_2.end
            )
