from unittest import TestCase
from datetime import datetime as DateTime
from datetime import timedelta as TimeDelta
from datetime import date as Date
from datetime import time as Time

from scheduler import Scheduler
from event import Event


class SchedulerTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.date = Date(year=2022, month=11, day=11)

        cls.time_0900 = Time(hour=9, minute=0)
        cls.time_0930 = Time(hour=9, minute=30)
        cls.time_1000 = Time(hour=10, minute=0)
        cls.time_1030 = Time(hour=10, minute=30)
        cls.time_1100 = Time(hour=11, minute=0)
        cls.time_1700 = Time(hour=17, minute=0)
        cls.time_1800 = Time(hour=18, minute=0)

        cls.event_0900_to_0930 = Event(
            start=DateTime.combine(cls.date, cls.time_0900),
            end=DateTime.combine(cls.date, cls.time_0930),
            name='Meeting between 09:00 and 09:30'
        )
        cls.event_0930_to_1000 = Event(
            start=DateTime.combine(cls.date, cls.time_0930),
            end=DateTime.combine(cls.date, cls.time_1000),
            name='Meeting between 09:30 and 10:00'
        )
        cls.event_0900_to_1000 = Event(
            start=DateTime.combine(cls.date, cls.time_0900),
            end=DateTime.combine(cls.date, cls.time_1000),
            name='Meeting between 09:00 and 10:00'
        )
        cls.event_1000_to_1030 = Event(
            start=DateTime.combine(cls.date, cls.time_1000),
            end=DateTime.combine(cls.date, cls.time_1030),
            name='Meeting between 10:00 and 10:30'
        )
        cls.event_1030_to_1100 = Event(
            start=DateTime.combine(cls.date, cls.time_1030),
            end=DateTime.combine(cls.date, cls.time_1100),
            name='Meeting between 10:30 and 11:00'
        )
        cls.event_1000_to_1100 = Event(
            start=DateTime.combine(cls.date, cls.time_1000),
            end=DateTime.combine(cls.date, cls.time_1100),
            name='Meeting between 10:00 and 11:00'
        )
        cls.event_1700_to_1800 = Event(
            start=DateTime.combine(cls.date, cls.time_1700),
            end=DateTime.combine(cls.date, cls.time_1800),
            name='Meeting between 17:00 and 18:00'
        )
        cls.event_0900_to_1800 = Event(
            start=DateTime.combine(cls.date, cls.time_0900),
            end=DateTime.combine(cls.date, cls.time_1800),
            name='Meeting between 09:00 and 18:00'
        )

    def setUp(self) -> None:
        # Set up new scheduler before each test.
        self.scheduler = Scheduler()

    def test_schedule(self):
        events = [
            self.event_0900_to_0930,
            self.event_0930_to_1000
        ]
        self.scheduler._schedule[self.date] = events
        schedule = self.scheduler.schedule
        # Edit specific event.
        schedule[self.date][0].name = 'some random name'
        self.assertListEqual(self.scheduler._schedule[self.date], events)
        # Edit list of events.
        schedule[self.date].pop()
        self.assertListEqual(self.scheduler._schedule[self.date], events)
        # Edit schedule dict.
        schedule.pop(self.date)
        self.assertListEqual(self.scheduler._schedule[self.date], events)

    def test_schedule_event(self):
        # Assert events are added in the correct order.
        self.scheduler.schedule_event(self.event_0930_to_1000)
        self.scheduler.schedule_event(self.event_1030_to_1100)
        self.scheduler.schedule_event(self.event_1000_to_1030)
        self.scheduler.schedule_event(self.event_0900_to_0930)
        self.assertListEqual(self.scheduler._schedule[self.date], [
            self.event_0900_to_0930,
            self.event_0930_to_1000,
            self.event_1000_to_1030,
            self.event_1030_to_1100
        ])

    def test_schedule_event__reschedule_same_day(self):
        self.scheduler.schedule_event(self.event_0900_to_0930)
        self.scheduler.schedule_event(self.event_0900_to_1000)
        self.assertListEqual(self.scheduler._schedule[self.date], [
            self.event_0900_to_0930,
            Event(
                start=DateTime.combine(self.date, self.time_0930),
                end=DateTime.combine(self.date, self.time_1030),
                name=self.event_0900_to_1000.name
            )
        ])

    def test_schedule_event__reschedule_next_day(self):
        self.scheduler.schedule_event(self.event_0900_to_1800)
        self.scheduler.schedule_event(self.event_0900_to_1000)
        next_day = Date(year=2022, month=11, day=14)
        self.assertDictEqual(self.scheduler._schedule, {
            self.date: [
                self.event_0900_to_1800
            ],
            next_day: [
                Event(
                    start=DateTime.combine(next_day, self.time_0900),
                    end=DateTime.combine(next_day, self.time_1000),
                    name=self.event_0900_to_1000.name
                )
            ]
        })

    def test_get_availabilities__no_events(self):
        availabilities = self.scheduler.get_availabilities(self.date)
        self.assertListEqual(availabilities, [
            Scheduler.Availability(
                start=DateTime.combine(self.date, self.time_0900),
                end=DateTime.combine(self.date, self.time_1800)
            )
        ])

    def test_get_availabilities__multiple_events(self):
        self.scheduler._schedule[self.date] = [
            self.event_0930_to_1000,
            self.event_1030_to_1100
        ]
        availabilities = self.scheduler.get_availabilities(self.date)
        self.assertListEqual(availabilities, [
            Scheduler.Availability(
                start=DateTime.combine(self.date, self.time_0900),
                end=DateTime.combine(self.date, self.time_0930)
            ),
            Scheduler.Availability(
                start=DateTime.combine(self.date, self.time_1000),
                end=DateTime.combine(self.date, self.time_1030)
            ),
            Scheduler.Availability(
                start=DateTime.combine(self.date, self.time_1100),
                end=DateTime.combine(self.date, self.time_1800)
            )
        ])

    def test_get_availabilities__event_at_start_of_day(self):
        self.scheduler._schedule[self.date] = [
            self.event_0900_to_0930
        ]
        availabilities = self.scheduler.get_availabilities(self.date)
        self.assertListEqual(availabilities, [
            Scheduler.Availability(
                start=DateTime.combine(self.date, self.time_0930),
                end=DateTime.combine(self.date, self.time_1800)
            )
        ])

    def test_get_availabilities__event_at_end_of_day(self):
        self.scheduler._schedule[self.date] = [
            self.event_1700_to_1800
        ]
        availabilities = self.scheduler.get_availabilities(self.date)
        self.assertListEqual(availabilities, [
            Scheduler.Availability(
                start=DateTime.combine(self.date, self.time_0900),
                end=DateTime.combine(self.date, self.time_1700)
            )
        ])

    def test_get_availabilities__event_at_start_and_end_of_day(self):
        self.scheduler._schedule[self.date] = [
            self.event_0900_to_0930,
            self.event_1700_to_1800
        ]
        availabilities = self.scheduler.get_availabilities(self.date)
        self.assertListEqual(availabilities, [
            Scheduler.Availability(
                start=DateTime.combine(self.date, self.time_0930),
                end=DateTime.combine(self.date, self.time_1700)
            )
        ])

    def test_get_availabilities__fully_booked(self):
        self.scheduler._schedule[self.date] = [
            self.event_0900_to_1800
        ]
        availabilities = self.scheduler.get_availabilities(self.date)
        self.assertListEqual(availabilities, [])

    def test_get_next_valid_date(self):
        date = Date(year=2022, month=11, day=12)
        date = self.scheduler.get_next_valid_date(date)
        self.assertEqual(date, Date(year=2022, month=11, day=14))

    def test_get_next_availability(self):
        self.scheduler._schedule[self.date] = [
            self.event_0930_to_1000,
            self.event_1030_to_1100
        ]
        start = DateTime.combine(self.date, self.time_1000)
        start, end = self.scheduler.get_next_availability(start, TimeDelta(hours=1))
        self.assertEqual(start, DateTime.combine(self.date, self.time_1100))
        self.assertEqual(end, DateTime.combine(self.date, Time(hour=12, minute=0)))

    def test_reschedule_invalid_event(self):
        name = 'some meeting'
        event = self.scheduler.reschedule_invalid_event(
            start=DateTime.combine(self.date, Time(hour=19, minute=0)),
            end=DateTime.combine(self.date, Time(hour=20, minute=0)),
            name=name
        )
        date = Date(year=2022, month=11, day=14)
        self.assertEqual(event, Event(
            start=DateTime.combine(date, self.time_0900),
            end=DateTime.combine(date, self.time_1000),
            name=name
        ))
        self.assertListEqual(self.scheduler._schedule[date], [event])

    def test_reschedule_overlapping_event(self):
        self.scheduler._schedule[self.date] = [
            self.event_0930_to_1000
        ]
        self.scheduler.reschedule_overlapping_event(self.event_0900_to_1000)
        self.assertListEqual(self.scheduler._schedule[self.date], [
            self.event_0930_to_1000,
            Event(
                start=DateTime.combine(self.date, self.time_1000),
                end=DateTime.combine(self.date, self.time_1100),
                name=self.event_0900_to_1000.name
            )
        ])