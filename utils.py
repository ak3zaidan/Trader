from enum import Enum

class Interval(Enum):
    ONE_DAY_1SEC = ("1 D", "1 sec")
    ONE_DAY_5SEC = ("1 D", "5 secs")
    ONE_DAY_15SEC = ("1 D", "15 secs")
    ONE_DAY_30SEC = ("1 D", "30 secs")

    ONE_DAY_1MIN = ("1 D", "1 min")
    ONE_DAY_2MIN = ("1 D", "2 mins")
    ONE_DAY_5MIN = ("1 D", "5 mins")
    ONE_DAY_15MIN = ("1 D", "15 mins")
    ONE_DAY_30MIN = ("1 D", "30 mins")

    ONE_WEEK_1MIN = ("1 W", "1 min")
    ONE_WEEK_2MIN = ("1 W", "2 mins")
    ONE_WEEK_5MIN = ("1 W", "5 mins")
    ONE_WEEK_15MIN = ("1 W", "15 mins")
    ONE_WEEK_30MIN = ("1 W", "30 mins")
    ONE_WEEK_1HOUR = ("1 W", "1 hour")

    ONE_MONTH_1HOUR = ("1 M", "1 hour")
    ONE_MONTH_1DAY = ("1 M", "1 day")

    THREE_MONTH_1DAY = ("3 M", "1 day")
    SIX_MONTH_1DAY = ("6 M", "1 day")

    ONE_YEAR_1DAY = ("1 Y", "1 day")
    ONE_YEAR_1WEEK = ("1 Y", "1 week")

    def __init__(self, duration: str, bar_size: str):
        self.duration = duration
        self.bar_size = bar_size
