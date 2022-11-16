from datetime import datetime as DateTime
from datetime import timedelta as TimeDelta
import math


def round_up_datetime(datetime: DateTime, timedelta: TimeDelta):
    return DateTime.min + (math.ceil((datetime - DateTime.min) / timedelta) * timedelta)
