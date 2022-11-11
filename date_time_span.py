from __future__ import annotations
import typing as t
from datetime import datetime as DateTime
from datetime import timedelta as TimeDelta
from datetime import date as Date
from itertools import groupby

from pydantic import BaseModel, Field, root_validator


class DateTimeSpan(BaseModel):
    """A span between start and end datetimes."""

    # autopep8: off
    class Error(ValueError):
        """Base error from which all other custom errors inherit from."""
        def __str__(self) -> str:
            return f'{self.__class__.__name__}: {super().__str__()}'
    class StartGreaterThanOrEqualToEndError(Error): pass
    # autopep8: on

    start: DateTime = Field()
    end: DateTime = Field()

    @root_validator(pre=True)
    def start_lt_end(cls, values: t.Dict[str, t.Any]):
        """Validate start is less than end."""
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
        """Checks if this span overlaps with another span.

        :param span: The other span to check for an overlap.
        :param equals: Whether self.start == span.end or span.start == self.end is an overlap.
        :return: A flag determining if this span overlaps with the other.
        """
        return (
            span.start <= self.start <= span.end
            or span.start <= self.end <= span.end
        ) if equals else (
            span.start <= self.start < span.end
            or span.start < self.end <= span.end
        )

    @staticmethod
    def merge(span_1: DateTimeSpan, span_2: DateTimeSpan):
        """Merge two overlapping spans.

        :param span_1: The first span to merge.
        :param span_2: The second span to merge.
        :return: The merged span. If the spans are not overlapping, None is returned.
        """
        if span_1.overlaps_with(span_2, equals=True):
            return DateTimeSpan(
                start=span_1.start if span_1.start <= span_2.start else span_2.start,
                end=span_1.end if span_1.end >= span_2.end else span_2.end
            )

    @classmethod
    def merge_many(cls, spans: t.List[DateTimeSpan]):
        """Merge the all the spans that can be merged together.

        :param spans: The list of spans to merge together.
        :return: A dict where the key is a date and the value is the merged spans for that date.
        """
        # Group events by date.
        def key(span: DateTimeSpan):
            return span.start.date()
        spans.sort(key=key)
        grouped_spans = {
            date: list(spans)
            for date, spans in groupby(spans, key=key)
        }

        # For each date, merge events' spans.
        merged_spans: t.Dict[Date, t.List[DateTimeSpan]] = {}
        for date, spans in grouped_spans.items():
            merged_spans[date] = []
            spans.sort()
            while spans:
                span = spans.pop(0)
                while spans:
                    merged_span = cls.merge(span, spans[0])
                    if merged_span is None:
                        break
                    else:
                        span = merged_span
                        spans.pop(0)
                merged_spans[date].append(span)
        return merged_spans
