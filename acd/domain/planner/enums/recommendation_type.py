from enum import StrEnum


class RecommendationType(StrEnum):
    APPLY = "apply"
    REVIEW_RESUME = "review_resume"
    REVIEW_COVER_LETTER = "review_cover_letter"
    IMPROVE_KEYWORDS = "improve_keywords"
    LOW_PRIORITY = "low_priority"
