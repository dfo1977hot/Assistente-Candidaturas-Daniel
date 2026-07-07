from enum import StrEnum


class StrategyType(StrEnum):
    APPLY_NOW = "apply_now"
    ADAPT_RESUME = "adapt_resume"
    ADAPT_RESUME_AND_COVER = "adapt_resume_and_cover"
    LOW_PRIORITY = "low_priority"
