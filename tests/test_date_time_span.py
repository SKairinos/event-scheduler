from datetime import datetime as DateTime
from datetime import date as Date
from datetime import time as Time
from datetime import timedelta as TimeDelta

from ._base import PyDanticTestCase
from date_time_span import DateTimeSpan


class TimeSpanTests(PyDanticTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.date = Date(year=2022, month=11, day=10)
        cls.dts_0900_1000 = DateTimeSpan(
            start=DateTime.combine(cls.date, Time(hour=9, minute=0)),
            end=DateTime.combine(cls.date, Time(hour=10, minute=0))
        )
        cls.dts_0900_0930 = DateTimeSpan(
            start=DateTime.combine(cls.date, Time(hour=9, minute=0)),
            end=DateTime.combine(cls.date, Time(hour=9, minute=30))
        )
        cls.dts_0930_1000 = DateTimeSpan(
            start=DateTime.combine(cls.date, Time(hour=9, minute=30)),
            end=DateTime.combine(cls.date, Time(hour=10, minute=0))
        )
        cls.dts_0830_0930 = DateTimeSpan(
            start=DateTime.combine(cls.date, Time(hour=8, minute=30)),
            end=DateTime.combine(cls.date, Time(hour=9, minute=30))
        )
        cls.dts_1000_1030 = DateTimeSpan(
            start=DateTime.combine(cls.date, Time(hour=10, minute=0)),
            end=DateTime.combine(cls.date, Time(hour=10, minute=30))
        )
        cls.dts_1400_1500 = DateTimeSpan(
            start=DateTime.combine(cls.date, Time(hour=14, minute=0)),
            end=DateTime.combine(cls.date, Time(hour=15, minute=0))
        )

    def test_root_validator__start_lt_end(self):
        # Assert start cannot be greater than end.
        self.assert_raises_validation_error(
            field_errors=[
                ('__root__', DateTimeSpan.StartGreaterThanOrEqualToEndError)
            ],
            model_type=DateTimeSpan,
            start=DateTime.combine(self.date, Time(hour=11, minute=0)),
            end=DateTime.combine(self.date, Time(hour=10, minute=0))
        )

        # Assert start cannot be equal to end.
        self.assert_raises_validation_error(
            field_errors=[
                ('__root__', DateTimeSpan.StartGreaterThanOrEqualToEndError)
            ],
            model_type=DateTimeSpan,
            start=DateTime.combine(self.date, Time(hour=10, minute=0)),
            end=DateTime.combine(self.date, Time(hour=10, minute=0))
        )

    def test_overlaps_with(self):
        self.assertTrue(self.dts_0900_1000.overlaps_with(self.dts_0900_0930, equals=True))
        self.assertTrue(self.dts_0900_1000.overlaps_with(self.dts_0900_0930, equals=False))
        self.assertTrue(self.dts_0900_0930.overlaps_with(self.dts_0900_1000, equals=True))
        self.assertTrue(self.dts_0900_0930.overlaps_with(self.dts_0900_1000, equals=False))
        self.assertTrue(self.dts_0900_0930.overlaps_with(self.dts_0930_1000, equals=True))
        self.assertFalse(self.dts_0900_0930.overlaps_with(self.dts_0930_1000, equals=False))
        self.assertTrue(self.dts_0930_1000.overlaps_with(self.dts_0900_0930, equals=True))
        self.assertFalse(self.dts_0930_1000.overlaps_with(self.dts_0900_0930, equals=False))

    def test_merge(self):
        date_time_span = DateTimeSpan.merge(self.dts_0900_1000, self.dts_0830_0930)
        self.assertEqual(date_time_span, DateTimeSpan(
            start=DateTime.combine(self.date, Time(hour=8, minute=30)),
            end=DateTime.combine(self.date, Time(hour=10, minute=0))
        ))

        date_time_span = DateTimeSpan.merge(date_time_span, self.dts_1000_1030)
        self.assertEqual(date_time_span, DateTimeSpan(
            start=DateTime.combine(self.date, Time(hour=8, minute=30)),
            end=DateTime.combine(self.date, Time(hour=10, minute=30))
        ))

        date_time_span = DateTimeSpan.merge(date_time_span, self.dts_1400_1500)
        self.assertIsNone(date_time_span)

    def test_timedelta(self):
        self.assertEqual(self.dts_0900_1000.timedelta, TimeDelta(hours=1))

    def test__lt__(self):
        self.assertLess(self.dts_0900_1000, self.dts_1000_1030)
