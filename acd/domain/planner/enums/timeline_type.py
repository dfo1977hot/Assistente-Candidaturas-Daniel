from enum import StrEnum


class TimelineType(StrEnum):
    TODAY = "today"
    TOMORROW = "tomorrow"
    THIS_WEEK = "this_week"
    LATER = "later"
