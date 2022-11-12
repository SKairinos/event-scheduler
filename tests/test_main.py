from unittest import TestCase
from datetime import datetime as DateTime
from datetime import date as Date
from datetime import time as Time
from io import StringIO
import subprocess
import sys

from main import print_schedule
from event import Event


class MainTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sys.stdout = StringIO()

    def open_main_process(self, *args: str):
        return subprocess.Popen(
            [sys.executable, 'main.py', *args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE
        )

    # def assert_schedule(self, schedule: Scheduler.Schedule):

    def test_input_events(self):
        main = self.open_main_process('--input-events')
        output, _ = main.communicate(input=b'\n'.join([
            b'2032/08/23 15:00 -> 2032/08/23 16:00 - Meet Jamie for coffee',
            b'2032/08/23 16:15 -> 2032/08/23 17:00 - Guitar lessons',
        ]) + b'\n\n')

        date = Date(year=2032, month=8, day=23)
        print_schedule({
            date: [
                Event(
                    start=DateTime.combine(date, Time(hour=15, minute=0)),
                    end=DateTime.combine(date, Time(hour=16, minute=0)),
                    name='Meet Jamie for coffee'
                ),
                Event(
                    start=DateTime.combine(date, Time(hour=16, minute=15)),
                    end=DateTime.combine(date, Time(hour=17, minute=0)),
                    name='Guitar lessons'
                )
            ]
        })
        self.assertIn(sys.stdout.getvalue().replace('\n', '\r\n'), output.decode('utf-8'))
