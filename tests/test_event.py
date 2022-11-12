from datetime import datetime as DateTime
from datetime import date as Date
from datetime import time as Time

from ._base import PyDanticTestCase
from event import Event


class EventTests(PyDanticTestCase):
    @classmethod
    def setUpClass(cls):
        cls.date = Date(year=2032, month=8, day=23)
        cls.start = Time(hour=15, minute=0)
        cls.end = Time(hour=16, minute=0)
        cls.event_str = '2032/08/23 15:00 -> 2032/08/23 16:00 - Meet Jamie for coffee'
        cls.event = Event(
            start=DateTime.combine(cls.date, cls.start),
            end=DateTime.combine(cls.date, cls.end),
            name='Meet Jamie for coffee'
        )

    def assert_event_equal(self, event_1: Event, event_2: Event):
        self.assertEqual(event_1.start, event_2.start)
        self.assertEqual(event_1.end, event_2.end)
        self.assertEqual(event_1.name, event_2.name)

    def test_validator__valid_weekday(self):
        # Assert cannot meet on Saturday.
        self.assert_raises_validation_error(
            field_errors=[
                ('start', Event.InvalidWeekDayError),
                ('end', Event.InvalidWeekDayError)
            ],
            model_type=Event,
            start=DateTime(year=2032, month=11, day=13, hour=9, minute=0),
            end=DateTime(year=2032, month=11, day=13, hour=10, minute=0),
            name='Meeting on Saturday'
        )

        # Assert cannot meet on Sunday.
        self.assert_raises_validation_error(
            field_errors=[
                ('start', Event.InvalidWeekDayError),
                ('end', Event.InvalidWeekDayError)
            ],
            model_type=Event,
            start=DateTime(year=2032, month=11, day=14, hour=9, minute=0),
            end=DateTime(year=2032, month=11, day=14, hour=10, minute=0),
            name='Meeting on Sunday'
        )

    def test_validator__valid_time(self):
        # Assert cannot start or end before start of day.
        self.assert_raises_validation_error(
            field_errors=[
                ('start', Event.InvalidTimeError),
                ('end', Event.InvalidTimeError)
            ],
            model_type=Event,
            start=DateTime(year=2032, month=11, day=10, hour=8, minute=0),
            end=DateTime(year=2032, month=11, day=10, hour=8, minute=30),
            name='Meeting before 9am'
        )

        # Assert cannot start or end after end of day.
        self.assert_raises_validation_error(
            field_errors=[
                ('start', Event.InvalidTimeError),
                ('end', Event.InvalidTimeError)
            ],
            model_type=Event,
            start=DateTime(year=2032, month=11, day=10, hour=18, minute=30),
            end=DateTime(year=2032, month=11, day=10, hour=19, minute=0),
            name='Meeting after 6pm'
        )

    def test_validator__not_in_the_past(self):
        # Assert cannot start or end before start of day.
        self.assert_raises_validation_error(
            field_errors=[
                ('start', Event.InThePastError),
                ('end', Event.InThePastError)
            ],
            model_type=Event,
            start=DateTime(year=2000, month=11, day=10, hour=9, minute=0),
            end=DateTime(year=2000, month=11, day=10, hour=9, minute=30),
            name='Meeting in the past'
        )

    def test_validator__not_end_of_day(self):
        # Assert cannot start meeting at end of day.
        self.assert_raises_validation_error(
            field_errors=[
                ('start', Event.EndOfDayError),
                ('end', Event.InvalidTimeError)
            ],
            model_type=Event,
            start=DateTime(year=2032, month=11, day=10, hour=18, minute=0),
            end=DateTime(year=2032, month=11, day=10, hour=18, minute=30),
            name='Meeting starting at end of day'
        )

        # Assert can end meeting at end of day.
        Event(
            start=DateTime(year=2032, month=11, day=10, hour=17, minute=30),
            end=DateTime(year=2032, month=11, day=10, hour=18, minute=0),
            name='Meeting ending at end of day'
        )

    def test_validator__not_start_of_day(self):
        # Assert cannot end meeting at start of day.
        self.assert_raises_validation_error(
            field_errors=[
                ('start', Event.InvalidTimeError),
                ('end', Event.StartOfDayError)
            ],
            model_type=Event,
            start=DateTime(year=2032, month=11, day=10, hour=8, minute=30),
            end=DateTime(year=2032, month=11, day=10, hour=9, minute=0),
            name='Meeting ending at start of day'
        )

        # Assert can start meeting at start of day.
        Event(
            start=DateTime(year=2032, month=11, day=10, hour=9, minute=0),
            end=DateTime(year=2032, month=11, day=10, hour=9, minute=30),
            name='Meeting starting at start of day'
        )

    def test_root_validator__lte_max_timedelta(self):
        # Assert time between start and end cannot exceed max timedelta.
        self.assert_raises_validation_error(
            field_errors=[
                ('__root__', Event.TimeDeltaTooLargeError)
            ],
            model_type=Event,
            start=DateTime(year=2032, month=11, day=9, hour=9, minute=0),
            end=DateTime(year=2032, month=11, day=9, hour=19, minute=0),
            name='Meeting starting at end of day'
        )

        # Assert start cannot be on different date to end.
        self.assert_raises_validation_error(
            field_errors=[
                ('__root__', Event.TimeDeltaTooLargeError)
            ],
            model_type=Event,
            start=DateTime(year=2032, month=11, day=9, hour=9, minute=0),
            end=DateTime(year=2032, month=11, day=10, hour=10, minute=0),
            name='Meeting starting at end of day'
        )

    def test__str__(self):
        # Assert stringified object is formatted as expected.
        self.assertEqual(str(self.event), self.event_str)

    def test__eq__(self):
        self.assertEqual(self.event, self.event)
        self.assertNotEqual(self.event, Event(
            start=self.event.start,
            end=self.event.end,
            name=self.event.name + ' something random',
        ))

    def test_fields_from_str(self):
        # Assert event object is created from string.
        fields = Event.fields_from_str(self.event_str)
        self.assert_event_equal(Event(**fields), self.event)

    def test_fields_from_str__invalid_format(self):
        # Assert invalid format.
        with self.assertRaises(Event.InvalidFormatError):
            Event.fields_from_str('2022/08/23 15:00 -> 2022/08/23 16:00')

        # Assert invalid DateTime format.
        with self.assertRaises(Event.InvalidDateTimeFormatError):
            Event.fields_from_str('2022/08/23 15:00 -> 2022/08/23 - Hello World')
