import typing as t
from collections import defaultdict, OrderedDict
from datetime import datetime as DateTime
from datetime import timedelta as TimeDelta
from datetime import date as Date
from datetime import time as Time

from event import Event
from date_time_span import DateTimeSpan
import utilities as utils


class Scheduler:
    """This will schedule events based on availability."""

    Schedule = t.OrderedDict[Date, t.List[Event]]

    class Availability(DateTimeSpan):
        """A span representing an availability in the schedule."""
        pass

    def __init__(self) -> None:
        # Schedule is a dict where the key is a date and the value is a list of events in order.
        self._schedule: t.DefaultDict[Date, t.List[Event]] = defaultdict(list)

    @property
    def schedule(self) -> Schedule:
        """Create a deep copy of the original schedule so that it may not be directly modified.

        :return: A deep copy of the schedule ordered by date.
        """
        ordered_dates = list(self._schedule.keys())
        ordered_dates.sort()
        return OrderedDict([
            (date, [event.copy() for event in self._schedule[date]])
            for date in ordered_dates
        ])

    def get_availabilities(self, date: Date):
        """Get all the unused datetime spans for a given date.

        :param date: The date to get availabilities for.
        :return: The availabilities for that date.
        """
        availabilities: t.List[Scheduler.Availability] = []
        start_of_day = DateTime.combine(date, Event._start_of_day)
        end_of_day = DateTime.combine(date, Event._end_of_day)

        events = self._schedule[date]
        if events:
            cursor = start_of_day
            spans = DateTimeSpan.merge_many(events)[date]
            for span, next_span in zip(spans, spans[1:] + [None]):
                # Cursor is at start of span.
                if cursor == span.start:
                    cursor = span.end
                    if next_span is not None:
                        availabilities.append(self.Availability(start=cursor, end=next_span.start))
                        cursor = next_span.end
                    elif cursor != end_of_day:
                        availabilities.append(self.Availability(start=cursor, end=end_of_day))

                # Cursor is behind span.
                elif cursor < span.start:
                    availabilities.append(self.Availability(start=cursor, end=span.start))
                    cursor = span.end
                    if next_span is None and cursor != end_of_day:
                        availabilities.append(self.Availability(start=cursor, end=end_of_day))
        else:
            availabilities.append(self.Availability(start=start_of_day, end=end_of_day))

        return availabilities

    def get_next_availability(self, start: DateTime, timedelta: TimeDelta):
        """Get the next availability for an event based on its original start and duration. A
        valid availability is one that's in the future and on an allowed week day. 

        :param start: The original start of the event.
        :param timedelta: The duration of the event.
        :return: When the event can next start and end.
        """

        def set_start_to_next_valid_date():
            nonlocal start
            date = start.date() + TimeDelta(days=1)
            while date.weekday() not in Event._valid_weekdays:
                date += TimeDelta(days=1)
            start = DateTime.combine(date, Time())

        def refresh_start():
            nonlocal start
            min_start = DateTime.now()
            # Start must at least be now.
            if start < min_start:
                start = utils.round_up_datetime(min_start, TimeDelta(minutes=1))
            # Start must be on a valid weekday.
            if start.date().weekday() not in Event._valid_weekdays:
                set_start_to_next_valid_date()

        # Ensure start is at least now and on a valid weekday.
        refresh_start()
        while True:
            # Get availabilities for start date.
            date = start.date()
            for availability in self.get_availabilities(date):
                # If availability's duration is less than event's, get next availability.
                if availability.timedelta < timedelta:
                    continue

                # Refresh start after elapsed processing time.
                # If date has incremented, get availabilities for the next date.
                refresh_start()
                if start.date() != date:
                    break

                # If availability's start is >= event's, set event's start to availability's.
                if availability.start >= start:
                    start = availability.start
                # Else validate if event can fit inside availability from event's original start.
                elif (availability.end - start) < timedelta:
                    continue

                # Return new start and end.
                return start, start + timedelta

            # At this point, no suitable availabilities were found.
            # If date did not increment during processing, get availabilities for next valid date.
            if start.date() == date:
                set_start_to_next_valid_date()

    def reschedule_overlapping_event(self, event: Event):
        """Edits an overlapping event's start and end to the next availability and adds it to the schedule.

        :param event: The overlapping event to reschedule.
        """
        # Set event's datetime span to next availability.
        start, end = self.get_next_availability(event.start, event.timedelta)
        event.start, event.end = start, end
        self.schedule_event(event)

    def reschedule_invalid_event(
        self,
        start: DateTime,
        end: DateTime,
        name: str,
        created_at: DateTime
    ):
        """Creates a new event at the next availability for an invalid event and adds it to the schedule.

        :param start: The event's original start.
        :param end: The event's original end.
        :param name: The event's original name.
        :return: A valid event with its start and end set at the next availability.
        """
        # Create event at next availability.
        start, end = self.get_next_availability(start, timedelta=end - start)
        event = Event(start=start, end=end, name=name, created_at=created_at)
        self.schedule_event(event)
        return event

    def schedule_event(self, event: Event) -> bool:
        """Schedules an event at the requested datetime span. If the event overlaps with an existing
        event, it will be rescheduled at next availability.

        :param event: The event to schedule.
        :return: A flag denoting if the event was overlapping and rescheduled.
        """
        # Get all events for given date.
        events = self._schedule[event.start.date()]

        for i, current_event in enumerate(events):
            # If event overlaps with current event, reschedule it.
            if event.overlaps_with(current_event, equals=False):
                self.reschedule_overlapping_event(event)
                return True
            # If event ends before current event starts, insert it before current event.
            if event.end <= current_event.start:
                events.insert(i, event)
                return False

        # If event starts after current event ends and no next event, append event to end.
        events.append(event)
        return False
