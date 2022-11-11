import typing as t
from collections import defaultdict
from datetime import datetime as DateTime
from datetime import timedelta as TimeDelta
from datetime import date as Date
from datetime import time as Time

from event import Event
from date_time_span import DateTimeSpan


class Scheduler:

    Schedule = t.DefaultDict[Date, t.List[Event]]

    class Availability(DateTimeSpan):
        pass

    def __init__(self) -> None:
        self._schedule: Scheduler.Schedule = defaultdict(list)

    @property
    def schedule(self) -> Schedule:
        """Create a deep copy of the original schedule so that it may not be directly written to.

        :return: A deep copy of the schedule.
        """
        return {
            date: [event.copy() for event in events]
            for date, events in self._schedule.items()
        }

    def schedule_event(self, event: Event):
        # Get all events for given date.
        date = event.start.date()
        events = self._schedule[date]

        # Handle 1st event.
        if not events:
            events.append(event)
            return False

        # Handle 2nd+ event.
        current_and_next_events = zip(events, events[1:] + [None])
        for i, (current_event, next_event) in enumerate(current_and_next_events):
            # Overlapping events.
            if event.overlaps_with(current_event, equals=False):
                self.reschedule_overlapping_event(event)
                return True
            else:
                if event.end <= current_event.start:
                    events.insert(i, event)
                    return False
                elif current_event.end <= event.start:
                    if next_event is None:
                        events.append(event)
                        return False
                    elif event.end <= next_event.start:
                        events.insert(i + 1, event)
                        return False
                    else:
                        self.reschedule_overlapping_event(event, events)
                        return True

    def get_availabilities(self, date: Date):
        availabilities: t.List[Scheduler.Availability] = []
        start_of_day = DateTime.combine(date, Event._start_of_day)
        end_of_day = DateTime.combine(date, Event._end_of_day)

        events = self._schedule[date]
        if events:
            cursor = start_of_day
            spans = Event.merge_date_time_spans(events)[date]
            for span, next_span in zip(spans, spans[1:] + [None]):
                # Cursor is at start of text span.
                if cursor == span.start:
                    cursor = span.end
                    if next_span is not None:
                        availabilities.append(self.Availability(start=cursor, end=next_span.start))
                        cursor = next_span.end
                    elif cursor != end_of_day:
                        availabilities.append(self.Availability(start=cursor, end=end_of_day))

                # Cursor is behind text span.
                elif cursor < span.start:
                    availabilities.append(self.Availability(start=cursor, end=span.start))
                    cursor = span.end
                    if next_span is None and cursor != end_of_day:
                        availabilities.append(self.Availability(start=cursor, end=end_of_day))
        else:
            availabilities.append(self.Availability(start=start_of_day, end=end_of_day))

        return availabilities

    def get_next_valid_date(self, date: Date):
        date += TimeDelta(days=1)
        while date.weekday() not in Event._valid_days:
            date += TimeDelta(days=1)
        return date

    def get_next_availability(self, start: DateTime, timedelta: TimeDelta):
        date = start.date()

        # Get next valid date if on an invalid weekday.
        if date.weekday() not in Event._valid_days:
            date = self.get_next_valid_date(date)

        while True:
            for availability in self.get_availabilities(date):
                if availability.start >= start and availability.timedelta >= timedelta:
                    return availability.start, availability.start + timedelta
            date = self.get_next_valid_date(date)

    def reschedule_overlapping_event(self, event: Event):
        # Set event's datetime span to next availability
        start, end = self.get_next_availability(event.start, event.timedelta)
        event.start, event.end = start, end
        self.schedule_event(event)

    def reschedule_invalid_event(self, start: DateTime, end: DateTime, name: str):
        # Create event at next availability.
        start, end = self.get_next_availability(start, timedelta=end - start)
        event = Event(start=start, end=end, name=name)
        self.schedule_event(event)
        return event
